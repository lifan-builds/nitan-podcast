# Design

## Editorial model

Keep the existing evidence, engagement, and model-review pipeline, but add a source-class-aware opportunity-cost layer. Editorial score remains useful inside a comparable class; it is not sufficient across classes when a maintenance changelog can outscore a broadly consequential provider/model change.

Each representative carries a controlled `editorial_class` such as `major_development`, `maintenance_release`, `research`, or `community_theme`. Classification comes from source type, release/version structure, category, and existing metadata—not named vendors or story titles. Final review priority starts with the model decision and score, then applies class rules:

- maintenance releases receive a substantial priority penalty unless the review judges impact, novelty, and audience breadth exceptional;
- research must clear a higher consequence/evidence/actionability threshold than normal product news;
- community themes may rank strongly from attention and builder consequence, but remain non-podcast-ready without qualifying sources;
- every class must clear a minimum quality floor before quotas are filled.

The editorial prompt explicitly asks the reviewer to consider the opportunity cost of one of ten slots and to distinguish broad changed assumptions from work relevant mainly to current users of one component.

## Freshness boundary

Use the configured review cutoff minus exactly 72 hours as the live collection start. Snapshot history remains available for measuring deltas, but historical items older than the cutoff cannot re-enter preprocessing. This separates metric baselines from editorial eligibility.

## Theme consolidation

Extend approved X panel configuration with organization affiliations. Collection preserves both the account identity and affiliated organization. Clustering derives controlled mentioned-organization and salient-topic metadata from configured organizations, explicit product families, titles, and summaries.

After canonical URL and explicit product-family matching, items may share a theme when they have the same affiliated/mentioned organization or product and sufficient salient-topic overlap. This joins, for example, an organization representative's post and community discussion about the same policy without introducing a story-specific alias. Conservative thresholds prevent all news from a large organization collapsing together.

## Review selection

Build reviewed records, compute `review_priority`, remove candidates below their class quality floor, and then attempt the six-community/four-primary mix with existing organization/product diversity plus one-per-theme. Shortfalls are explicit; there is no filler backfill from rejected low-value classes.

Artifacts expose `editorial_class`, priority adjustments, freshness cutoff, and exclusion/shortfall reasons so the user can understand the judgment without reverse-engineering scores.

## Compatibility and rollback

Keep the authenticated X health contract, strict batched GPT-5.6 Terra review, response schema, read-only workflow permissions, and review artifact filenames. Rollback is limited to the follow-up AI Builder commits. No public feed, site, audio, release, or R2 path changes.
