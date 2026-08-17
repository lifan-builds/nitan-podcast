# Implementation Plan

1. Add collection-health contracts and a bounded X retry path that preserves likes/retweets, account success, and in-window post counts without leaking authenticated state.
2. Add explicit product-family metadata and product-first clustering for versioned release sources.
3. Preserve X/HN/Hugging Face/GitHub community metadata through preprocessing and build a deterministic 12-community/12-primary model-review pool.
4. Extend the strict editorial packet with controlled community context while keeping exact schema coverage and evidence authority unchanged.
5. Select review output with the approved 6-community/4-primary mix and one-per-organization/product-family rule; require qualifying evidence for `podcast_ready`.
6. Embed source health, class, product family, mix counts, and shortfalls in matching JSON/Markdown artifacts. Fail without a top ten when X health is below the approved threshold.
7. Add focused tests for X retry/engagement/health, unhealthy-X fail-closed behavior, product-family collapse, signal aggregation, 12/12 admission, 6/4 selection, diversity, and signal-only podcast readiness.
8. Run the focused and full offline quality gates, commit and push, regenerate August 17, download and compare the review, and verify public hashes/releases/R2 remain unchanged.

## Validation Commands

- `.venv/bin/python -m pytest tests/test_collectors.py tests/test_editorial.py tests/test_pipeline.py tests/test_review.py tests/test_workflow.py`
- `.venv/bin/python -m pytest`
- `ruff check .`
- `mypy --ignore-missing-imports --disable-error-code import-untyped src`
- `.venv/bin/python -m compileall -q src scripts tests`
- `.venv/bin/python -c 'import yaml; yaml.safe_load(open(".github/workflows/daily.yml"))'`
- `gh workflow run daily.yml -f episode_date=2026-08-17`
- `gh run watch <run-id> --exit-status`

## Risks and rollback points

- High engagement must not be confused with evidence; tests must keep signal-only candidates non-podcast-ready.
- Product-family clustering must not merge unrelated products from one large organization; use explicit configured identities rather than organization alone.
- X diagnostics must exclude stderr, response bodies, cookies, and authenticated URLs.
- Strict 6/4 and diversity constraints may yield fewer than ten when the source pool is weak; expose the shortfall instead of filling with duplicates.
- Do not issue concurrent or unbounded X retries; one retry per failed approved account keeps the live run bounded.
