# Design

## Review-only boundary

Add an explicit `review_only` pipeline mode and `--review-only` CLI flag. The GitHub Actions workflow always passes that flag during this evaluation period. The mode shares collection, snapshot enrichment, deterministic preprocessing, batched editorial review, exact coverage validation, and ledger writing with the episode path, then returns before `run_episode` or any audio/publication code.

The scheduled workflow always admits only the existing intended 6 AM Pacific slot during review mode, independent of `PUBLICATION_ENABLED`. Manual dispatch keeps the optional date input but no longer exposes a misleading shadow/audio choice.

## Review artifacts

After a valid editorial response, join every model decision back to its representative cluster and evidence sources. Sort by editorial score descending with cluster ID as a deterministic tie-breaker, then retain up to ten.

Write two date-keyed files under `build/review/`:

- `<date>.json`: structured top-10 candidates with rank, title, summary, organization, category, publication time, decision, podcast-ready boolean, full controlled editorial fields, and cited source IDs/URLs/authorities.
- `<date>.md`: a readable rendering of the same ordered records, including why-now, rationale, builder actions, caveats, score, decision, readiness, and source links.

The existing full editorial ledger remains the audit artifact, including deterministic rejects outside the top ten and sanitized failure metadata. The review artifact is generated after exact model coverage succeeds, so a collector or editorial infrastructure failure retains only the fail-closed ledger and never produces a partial top ten.

Podcast readiness uses the existing qualification rule: editorial `accept`, score at least 70, impact at least 3, and evidence at least 3. Review-only success does not require the normal three-story episode minimum.

## Workflow and artifact retention

Rename the execution step to reflect daily review, call `ai_builder_brief run --review-only`, and upload the existing `build/` tree. Remove public validation and commit steps from this workflow while review mode is active, making public mutation unreachable even if repository variables change.

## Compatibility and rollback

Do not modify `docs/`, RSS identity, R2 keys, releases, NotebookLM state, or the underlying episode path. The ordinary CLI remains capable of episode generation when called without `--review-only`, but the scheduled workflow cannot reach it during this evaluation period. Restoring podcast shadows later is an explicit workflow change after editorial review is complete.
