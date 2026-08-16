# Design

## Editorial review boundary

Keep `review_candidates` as the strict single-request primitive. Add a deterministic batching layer that slices the already pre-ranked packet into small fixed-size batches, calls the primitive once per batch, and concatenates decisions in input order. The pipeline performs its existing global exact-coverage validation after merging, so batching cannot silently omit or duplicate a cluster.

Each request retains the configured usage gate, pinned model, strict schema, localhost-only endpoint, and 60-second timeout. A failure in any batch aborts the review and returns no episode.

## Failure diagnostics

Introduce a small sanitized editorial exception carrying a stable category such as `usage_gate`, `timeout`, `proxy`, or `invalid_response`, plus the batch index when applicable. The pipeline writes only these controlled fields into ledger metadata. It must not write URLs containing keys, request headers, raw proxy responses, cookies, credentials, or full model output.

## Runner reliability

Wrap only the long-running episode command with macOS `caffeinate`; checkout and installation remain unchanged. This directly prevents the observed sleep interruption without introducing a resident background service.

Move attempt-slot calculation into a small testable helper. Scheduled cron entries become individually identifiable. The helper converts the intended UTC cron hour to Pacific local time for the run date, rather than using the delayed runner start hour. Pre-publication mode accepts only the intended 6 AM slot; publication mode accepts 6, 8, and 10 AM. Manual dispatch remains explicit and unchanged.

## Compatibility and rollback

No public schema, feed identity, GUID, URL, R2 layout, or Castforge contract changes are required. Rollback is a single AI Builder Brief commit. Publication stays disabled throughout the fix and validation.

