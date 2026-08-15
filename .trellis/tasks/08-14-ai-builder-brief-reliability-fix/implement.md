# Implementation Plan

1. Add deterministic editorial batching and controlled failure categories in the editorial client.
2. Record sanitized editorial failure metadata in unpublished ledgers while preserving fail-closed behavior.
3. Add focused tests for batch sizing/order, exact merged coverage, timeouts, invalid batches, and safe diagnostics.
4. Add a testable intended-schedule-slot helper and update the workflow to use identifiable cron slots.
5. Wrap the episode command with `caffeinate` on the macOS self-hosted runner.
6. Run the focused editorial/workflow tests, then the complete AI Builder Brief test suite.
7. Commit and push the reliability fix.
8. Dispatch one private `2026-08-11` regeneration, monitor it to completion, download the artifact, and validate editorial evidence, citations, audio duration, transcript, chapters, cleanup, and unchanged public state.

## Validation Commands

- `.venv/bin/python -m pytest tests/test_editorial.py tests/test_pipeline.py`
- `.venv/bin/python -m pytest`
- `gh workflow run daily.yml -f episode_date=2026-08-11 -f shadow=true`
- `gh run view <run-id> --log`

## Risk and rollback points

- Batch size that is still too large can reproduce the timeout; validate against the real 23-candidate fixture before the private rerun.
- Schedule mapping mistakes can create extra shadow attempts; tests must cover PDT and PST before pushing.
- Do not retry real NotebookLM generation after it has been reached on the same day.
- If validation fails, leave `PUBLICATION_ENABLED=false` and do not copy any shadow artifact into `docs/` or R2.

