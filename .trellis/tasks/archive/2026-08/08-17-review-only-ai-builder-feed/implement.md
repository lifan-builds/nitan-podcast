# Implementation Plan

1. Add deterministic review-record construction and JSON/Markdown writers for the top ten model-reviewed candidates.
2. Add `review_only` to `run_daily` and `--review-only` to the CLI; return a stable `review-ready` status after artifact creation and before minimum-story/audio handling.
3. Update the scheduled workflow to run only the daily review path, retain `build/`, and remove all public validation/commit branches from the job.
4. Add focused tests for ranking/tie-breaking, accepted-and-rejected inclusion, podcast-ready markers, JSON/Markdown parity, review-only success below three qualifying stories, and the hard stop before `run_episode`.
5. Run Ruff, mypy, the focused tests, the full offline suite, compile checks, and workflow YAML validation.
6. Commit and push the AI Builder Brief change, manually dispatch the August 17 review job, monitor it, download its artifact, inspect all ten entries and citations, and confirm public RSS, releases, R2, and NotebookLM were unchanged.

## Validation Commands

- `.venv/bin/ruff check .`
- `.venv/bin/mypy src`
- `.venv/bin/python -m pytest tests/test_pipeline.py tests/test_workflow.py`
- `.venv/bin/python -m pytest`
- `.venv/bin/python -m compileall -q src scripts tests`
- `.venv/bin/python -c 'import yaml; yaml.safe_load(open(".github/workflows/daily.yml"))'`
- `gh workflow run daily.yml -f episode_date=2026-08-17`
- `gh run watch <run-id> --exit-status`

## Risk and rollback points

- Ranking must not accidentally redefine podcast qualification; centralize or directly reuse the existing predicate and test rejected high-score cases.
- The workflow must not retain a hidden path to audio/public mutation; assert `--review-only` and absence of validation/commit steps in workflow tests.
- A live editorial failure should remain a successful no-publication outcome with its ledger available for diagnosis, not trigger audio or an automatic retry.
- Rollback is the single AI Builder Brief commit; public state is unaffected throughout.
