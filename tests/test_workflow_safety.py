"""Regression checks for the weekly publication workflow."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "weekly-export.yml").read_text(encoding="utf-8")
REQUIREMENTS = (ROOT / "requirements.txt").read_text(encoding="utf-8")


def _step(name: str) -> str:
    marker = f"      - name: {name}\n"
    start = WORKFLOW.index(marker)
    end = WORKFLOW.find("\n      - ", start + len(marker))
    return WORKFLOW[start:] if end == -1 else WORKFLOW[start:end]


def test_audio_failure_is_not_ignored() -> None:
    assert "continue-on-error" not in _step("Generate audio (NotebookLM)")


def test_audio_format_is_verified_before_publication_and_duration_reaches_rss() -> None:
    audio = _step("Generate audio (NotebookLM)")
    assert audio.index("scripts/prepare_audio.py") < audio.index("has_audio=true")
    assert "steps.audio.outputs.duration" in _step("Generate RSS feed and forum post")


def test_auth_is_checked_before_extraction_only_when_audio_is_needed() -> None:
    name = "Check NotebookLM login and notebook"
    assert WORKFLOW.index(name) < WORKFLOW.index("Extract and export Markdown")
    step = _step(name)
    for condition in (
        "steps.check.outputs.skip != 'true'",
        "inputs.skip_audio != true",
        "inputs.audio_url == ''",
    ):
        assert condition in step
    assert "continue-on-error" not in step


def test_failed_steps_are_not_reported_as_completed() -> None:
    summary = _step("Job summary")
    assert "Export: done" not in summary
    assert "RSS: updated" not in summary
    for step in ("export", "notebooklm_auth", "feed", "publish", "validate"):
        assert f"steps.{step}.outcome" in summary


def test_publication_runs_do_not_overlap_or_cancel_an_active_publish() -> None:
    assert "group: weekly-podcast-publication" in WORKFLOW
    assert "cancel-in-progress: false" in WORKFLOW


def test_publication_steps_require_a_released_audio_url() -> None:
    for name in (
        "Generate RSS feed and forum post",
        "Commit and push RSS feed",
        "Validate live feed",
    ):
        assert "steps.release.outputs.audio_url != ''" in _step(name)


def test_exports_are_retained_after_a_failure() -> None:
    assert "always()" in _step("Upload exports")


def test_actions_use_node24_releases() -> None:
    assert "actions/checkout@v5" in WORKFLOW
    assert "actions/upload-artifact@v7" in WORKFLOW


def test_nitan_explicitly_requests_chinese_audio() -> None:
    assert "NOTEBOOKLM_AUDIO_LANGUAGE: zh" in WORKFLOW


def test_castforge_dependency_is_pinned_in_requirements() -> None:
    assert "castforge @ git+https://github.com/lifan-builds/castforge.git@v0.1.3" in REQUIREMENTS
    assert "castforge.git@" not in WORKFLOW
    assert "$PY -m pip install -q -r requirements.txt" in WORKFLOW
