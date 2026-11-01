"""Offline checks for early failure and safe recovery diagnostics."""

import asyncio
from unittest.mock import AsyncMock

import pytest

pytest.importorskip("notebooklm")

from scripts import check_notebooklm_auth as preflight


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(preflight, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(preflight.logging, "disable", lambda *a: None)
    monkeypatch.setenv("NOTEBOOKLM_NOTEBOOK_ID", "test-notebook")
    monkeypatch.setenv("NOTEBOOKLM_STORAGE_PATH", "/tmp/podcast session.json")


def test_success_checks_configured_storage_and_notebook(monkeypatch):
    check = AsyncMock()
    monkeypatch.setattr(preflight, "check_access", check)
    assert preflight.main([]) == 0
    check.assert_awaited_once_with("/tmp/podcast session.json", "test-notebook")


def test_missing_notebook_fails_without_network(monkeypatch, capsys):
    monkeypatch.delenv("NOTEBOOKLM_NOTEBOOK_ID")
    check = AsyncMock()
    monkeypatch.setattr(preflight, "check_access", check)
    assert preflight.main([]) == 1
    check.assert_not_called()
    assert "NOTEBOOKLM_NOTEBOOK_ID" in capsys.readouterr().out


@pytest.mark.parametrize("error", [preflight.AuthError, FileNotFoundError])
def test_expired_or_missing_login_has_safe_matching_recovery(error, monkeypatch, capsys):
    monkeypatch.setattr(preflight, "check_access", AsyncMock(side_effect=error("SECRET_RESPONSE")))
    assert preflight.main([]) == 1
    output = capsys.readouterr().out
    assert "--storage '/tmp/podcast session.json' login" in output
    assert "--browser chrome --fresh" in output
    assert "SECRET_RESPONSE" not in output


def test_network_failure_does_not_claim_login_expired(monkeypatch, capsys):
    monkeypatch.setattr(preflight, "check_access", AsyncMock(side_effect=TimeoutError("SECRET_RESPONSE")))
    assert preflight.main([]) == 1
    output = capsys.readouterr().out
    assert "TimeoutError" in output
    assert "expired" not in output
    assert "SECRET_RESPONSE" not in output


def test_default_storage_uses_sdk_resolution(monkeypatch):
    monkeypatch.delenv("NOTEBOOKLM_STORAGE_PATH")
    monkeypatch.setattr(preflight, "get_storage_path", lambda: "/tmp/default-profile.json")
    check = AsyncMock()
    monkeypatch.setattr(preflight, "check_access", check)
    assert preflight.main([]) == 0
    check.assert_awaited_once_with("/tmp/default-profile.json", "test-notebook")


def test_access_checks_target_notebook_inside_client_context(monkeypatch):
    client = AsyncMock()
    client.__aenter__.return_value = client
    factory = lambda storage: client
    monkeypatch.setattr(preflight.NotebookLMClient, "from_storage", factory)
    asyncio.run(preflight.check_access("/tmp/session.json", "test-notebook"))
    client.notebooks.get.assert_awaited_once_with("test-notebook")
    client.__aexit__.assert_awaited_once()
