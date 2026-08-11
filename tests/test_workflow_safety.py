"""Regression checks for the weekly publication workflow."""

from pathlib import Path


WORKFLOW = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "weekly-export.yml"
).read_text(encoding="utf-8")


def _step(name: str) -> str:
    marker = f"      - name: {name}\n"
    start = WORKFLOW.index(marker)
    end = WORKFLOW.find("\n      - ", start + len(marker))
    return WORKFLOW[start:] if end == -1 else WORKFLOW[start:end]


def test_audio_failure_is_not_ignored() -> None:
    assert "continue-on-error" not in _step("Generate audio (NotebookLM)")


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
