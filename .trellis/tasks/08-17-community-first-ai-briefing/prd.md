# Community-first AI briefing redesign

## Goal

Redesign AI Builder Brief discovery and ranking so the daily top ten reflects the AI-builder community's most consequential themes and influencer conversations, not a list dominated by routine version releases or whichever official feeds have the highest fixed source scores.

## Background

- The August 17 review contained four Ollama entries and three OpenAI entries; separate release tags became separate clusters and the review ranking did not apply product/organization diversity.
- All 19 configured X accounts failed during the workflow, leaving zero influencer items in a 182-item snapshot. The authenticated CLI works now, so the live failure was transient rather than a permanently missing account.
- Even when X succeeds, the collector discards likes/retweets, gives every post a fixed score of 35, and deterministic preprocessing caps the model-review pool after higher-scored official sources. Influencer posts therefore rarely reach editorial review.
- Hacker News produced five signals, but signal-only items are deterministically rejected and their engagement does not propagate to a matching primary-source candidate.
- GitHub release tags use release-specific URLs and titles, so consecutive versions of the same repository are not consolidated into one product-family development.
- Community signals must guide discovery, momentum, and theme importance without becoming uncorroborated technical evidence.

## Requirements

- Treat X influencer posts, Hacker News discussion, Hugging Face activity, and repository momentum as first-class community signals for discovery and ranking.
- Preserve primary-source grounding for technical claims; community attention can elevate a theme but cannot establish unsupported capabilities or benchmarks.
- Consolidate same-product release activity into one theme for the rolling review window and allow at most one top-10 item per product family or organization.
- Carry engagement and corroboration metadata into editorial review instead of discarding it before the 24-candidate boundary.
- Construct community themes from multiple related signals where possible, rather than presenting isolated tweets as ten separate stories.
- Make transient X failure visible in source-health metadata and retain the other collected signals in the raw snapshot, but never emit a completed release-only top ten as representative of community trends.
- Keep review-only execution, ten accepted/rejected review entries, fail-closed editorial validation, read-only workflow permissions, and no podcast/publication side effects.
- Regenerate August 17 after implementation and compare the result with the original review.

## Out of Scope

- Treating popularity alone as factual evidence or automatically accepting a story because an influencer posted it.
- Publishing audio, RSS, Pages episodes, releases, or R2 objects.
- Scraping private X data, posting/liking/following, or changing the authenticated X account.
- Expanding to every social network in this iteration.

## Key Decisions

- The review targets six community-led themes and four major primary-source developments. Community-led themes may use influencer, HN, Hugging Face, or GitHub momentum for discovery and importance, but technical claims still require primary corroboration.
- X is required for a valid community-first review. The collector retries transient failures and records panel health; if X coverage remains unhealthy, the run retains source-health diagnostics and the fail-closed ledger but does not emit a top ten.
- The existing 19-account approved panel remains the influencer boundary. This task does not search arbitrary accounts or mutate X state.

## Acceptance Criteria

- [x] Multiple versions from one repository or product family collapse into one review theme, and no organization/product occupies more than one top-10 slot.
- [x] X engagement and HN/Hugging Face/GitHub momentum survive collection and influence candidate admission/ranking while technical claims remain source-grounded.
- [x] The candidate pool reserves meaningful room for community themes instead of excluding fixed-low-score signal sources before model review.
- [x] X unavailability is explicit in artifact health metadata and does not silently yield a release-centric top ten.
- [x] A healthy run successfully queries at least 80% of the approved X panel and obtains at least one in-window post; otherwise it emits no completed top ten.
- [x] Focused tests cover product-family deduplication, community-signal aggregation, candidate-pool balance, diversity, and unhealthy-X fail-closed behavior.
- [x] A regenerated August 17 review has ten distinct themes, contains the approved community/primary balance, and leaves all podcast/public state unchanged.
