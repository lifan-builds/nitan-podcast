# Design

## Source collection and health

Replace the bare source list at the pipeline boundary with a collection result containing source items plus controlled health metadata. Health reports configured/attempted/successful X accounts, valid in-window posts, and failed account names without stderr, cookies, command output, or authentication data.

The X reader performs the existing read-only `user-posts` call with one immediate retry for non-zero exit, timeout, invalid JSON, or invalid payload. Preserve `likes` and `rts` from the CLI response, derive bounded engagement and momentum fields, and keep the post attributed to its approved account. A valid X panel requires at least 80% account-query success and at least one in-window post. The local client currently passes 19/19 accounts; its recurring ClientTransaction warning is non-fatal because the commands return valid JSON with exit zero.

Write date-keyed source health before editorial review. A still-unhealthy panel returns `no-review-source-failure`, retains health plus a sanitized ledger, and creates no top-10 JSON/Markdown. Successful review artifacts embed the same source-health summary.

## Product-family and community grouping

Add explicit product-family metadata to release-feed and GitHub repository items. Product-family identity takes precedence over release-specific URLs when assigning clusters, collapsing all Ollama, vLLM, llama.cpp, or Transformers versions in the rolling window into one development. Review selection also permits at most one item per organization and product family.

Community signals keep their evidence role:

- approved X posts are attributed analysis with engagement metadata;
- Hacker News carries points/comments and remains signal evidence;
- Hugging Face trending/upvote data and GitHub measured deltas are community momentum attached to their primary artifacts;
- shared URLs or strong headline overlap attach community signals to the corresponding grounded development when possible;
- an isolated signal may enter the review pool as a community theme, but cannot become podcast-ready without qualifying evidence.

## Balanced candidate admission

Do not stop preprocessing after the 24 highest fixed source scores. Process deterministic exclusions, classify surviving clusters as community-led or primary-led, then admit a deterministic 24-candidate review pool with 12 slots for each class. Community-led means the cluster contains an approved X/HN signal or measured Hugging Face/GitHub community momentum; primary-led means it is important without such a signal.

Pass source types, aggregate community counts, X likes/retweets, HN points/comments, momentum, product family, and corroborating source IDs to the existing strict batched editorial review. Popularity changes admission and context, not factual authority or automatic acceptance.

## Top-10 review selection

Build all reviewed records first, then select six community-led and four primary-led records by editorial score with deterministic tie-breaking. Enforce one item per organization and product family across both groups. If a class lacks enough distinct candidates, include fewer rather than duplicate a product or manufacture filler, and report the mix shortfall in artifact metadata.

Podcast readiness continues to require the editorial score/impact/evidence thresholds plus qualifying source evidence. Signal-only themes may appear in the human review as accepted community observations or rejects, but remain `podcast_ready: false`.

## Compatibility and rollback

Keep GPT-5.6 Terra, batched exact coverage, the 60-second per-request timeout, review-only scheduling, read-only repository permission, public identities, and all no-audio/no-publication boundaries. Rollback is one AI Builder Brief commit. Regeneration uses the same August 17 date and replaces only ignored local/workflow review artifacts; public state remains immutable.
