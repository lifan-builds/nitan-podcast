# Editorial judgment for consequential AI news

## Goal

Make the daily AI Builder review feel editorially selective: surface developments that materially change what builders should know, choose, or reconsider, while excluding maintenance churn, ordinary paper flow, and stale stories. The user's examples express this taste and must not become title/vendor allowlists.

## Background

- The regenerated August 17 review correctly restored X and diversity, but ranked vLLM 0.27.0 first because a large release note scored highly on impact and actionability even though it is specialist serving-runtime maintenance rather than broadly important daily news.
- Hugging Face Daily Papers entered the community quota merely through paper upvotes; the resulting research item was credible but not exceptional enough to displace major product and policy developments.
- Anthropic watermarking, Gemini 3.7 Flash, and GPT-5.6 Ultrafast illustrate the desired editorial lens: changes to provider behavior, widely used model capability/cost, or a material API performance frontier can matter more than a dense version changelog.
- These examples are not mandatory inclusions. Under a strict three-day August 17 cutoff, the sampled Gemini and GPT posts are too old and should be excluded even though their story type is desirable.

## Requirements

- Use a strict rolling 72-hour window ending at the configured Pacific review cutoff. Do not admit older items from historical snapshots or older release entries.
- Rank by editorial consequence and opportunity cost: a top-ten item should displace alternatives because it changes a meaningful builder decision, affects a broad or strategically important audience, or reveals a consequential community/provider shift.
- Treat routine runtime/library versions, compatibility matrices, patch releases, release candidates, and long changelogs as maintenance by default. They may surface only when the development changes a broad assumption beyond existing users upgrading that component.
- Treat daily-paper placement and upvotes as discovery signals, not evidence that a paper deserves a top slot. Research must be unusually consequential, well-supported, and practically relevant to builders to survive final selection.
- Preserve community attention as importance context, never factual authority. Technical claims still require a primary artifact or two independent credible sources for podcast readiness.
- Consolidate multiple posts/articles about one underlying event into one review theme where configured account affiliation plus organization/product/topic overlap makes the relationship deterministic.
- Preserve the target of six community-led and four primary-led themes, but apply a quality floor before filling quotas. Emit fewer than ten rather than include low-value maintenance or ordinary research.
- Keep one item per organization/product family/theme, review-only execution, strict editorial coverage, sanitized health artifacts, and all no-audio/no-publication boundaries.
- Implement general source-class and editorial-principle rules. Do not hardcode boosts or acceptance for Anthropic, Gemini, GPT, OpenAI, Google, or the cited titles.

## Acceptance Criteria

- [ ] For an August 17 06:00 Pacific review, every collected/reviewed item is published at or after August 14 06:00 Pacific; older Gemini/GPT examples are absent despite matching the desired story type.
- [ ] A synthetic large but routine serving-runtime release ranks below a consequential provider-policy or major model/API change and does not become top merely from release-note breadth.
- [ ] A routine Daily Paper is excluded from the top ten; exceptional research can qualify only when its editorial scores and practical consequence clear the higher research bar.
- [ ] Related community and primary/analysis sources collapse into one theme using general affiliation/entity/topic metadata, preventing separate slots for the same watermarking-style event.
- [ ] Selection applies the quality floor before the 6/4 target and exposes shortfalls rather than adding filler.
- [ ] Focused tests cover the 72-hour boundary, maintenance penalty, exceptional-research gate, thematic consolidation, generality/no title allowlist, and quota shortfall behavior.
- [ ] A regenerated August 17 artifact is materially more consequential than the prior output, contains no stale items, and leaves feed/site/releases/R2 unchanged.

## Out of Scope

- Guaranteeing that the user's named examples appear when they fall outside the freshness window.
- Building a vendor/title allowlist or keyword-only recommender.
- Replacing source-grounded editorial review with raw engagement ranking.
- Podcast generation or publication.
