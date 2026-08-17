# Implementation Plan

1. Replace the seven-day editorial eligibility window with a strict 72-hour cutoff while preserving older snapshots only as metric baselines.
2. Add configured X account affiliations and controlled organization/topic metadata for general cross-source theme consolidation.
3. Classify candidates into major development, maintenance release, research, and community theme without named-story boosts.
4. Extend the editorial packet/prompt with opportunity-cost guidance and controlled class/context fields.
5. Compute class-aware review priority and quality floors; apply them before the 6/4 diversity selection and expose shortfalls.
6. Add artifact fields for freshness cutoff, editorial class, priority adjustment, and exclusion/shortfall reasons.
7. Add focused tests for the 72-hour boundary, old-snapshot exclusion, maintenance demotion, exceptional research, general theme consolidation, and no-filler quotas.
8. Run the focused and full offline quality gates, commit/push, regenerate August 17, compare with the prior review, and re-verify public immutability.

## Validation Commands

- `.venv/bin/python -m pytest tests/test_collectors.py tests/test_editorial.py tests/test_pipeline.py tests/test_review.py tests/test_workflow.py`
- `.venv/bin/python -m pytest`
- `ruff check .`
- `mypy --ignore-missing-imports --disable-error-code import-untyped src`
- `.venv/bin/python -m compileall -q src scripts tests`
- `.venv/bin/python -c 'import yaml; yaml.safe_load(open(".github/workflows/daily.yml")); yaml.safe_load(open("sources.yaml"))'`
- `gh workflow run daily.yml -f episode_date=2026-08-17`
- `gh run watch <run-id> --exit-status`

## Risks and rollback points

- Over-broad organization/topic clustering could merge unrelated stories; require both a controlled entity/product match and salient topic overlap.
- Class penalties must not categorically ban infrastructure or research; exceptional cases retain a documented path through the quality floor.
- A strict 72-hour window may produce fewer than ten items on quiet days; that is intentional and must appear as a shortfall.
- Named examples are validation illustrations only and must not appear in production ranking constants or allowlists.
