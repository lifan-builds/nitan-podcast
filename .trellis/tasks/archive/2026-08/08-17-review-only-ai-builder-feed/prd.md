# Review-only daily AI briefing

## Goal

Run AI Builder Brief as a daily editorial-review product for several days: collect current sources, review a broader top-10 set, and retain human-readable summaries and raw structured inputs without invoking NotebookLM, transcription, R2, RSS, or episode publication.

## Background

- The current scheduled path collects and reviews a bounded candidate pool, selects 3–6 qualifying clusters, writes an editorial ledger and `build/editorial-input/<date>.json`, and then immediately calls CastForge's `run_episode`, which writes the NotebookLM source document and generates audio.
- The private August 16 shadow produced three qualified stories and valid audio, but publication remains disabled while the workflow is evaluated.
- `PUBLICATION_ENABLED=false`, the public RSS feed is empty, and this review period must not create or publish episodes.
- The existing editorial ledger already records every reviewed candidate and its decision. The current podcast input contains only selected sources and caps selection at six stories.

## Requirements

- Scheduled and manually dispatched jobs run the same review-only pipeline and stop before all podcast/audio stages.
- Keep the existing source collection, deterministic preprocessing, batched GPT-5.6 Terra editorial review, evidence rules, and sanitized failure diagnostics.
- Retain a date-keyed raw JSON review artifact and a date-keyed human-readable Markdown summary suitable for holistic review.
- Surface the ten highest-ranked model-reviewed candidates, including editorial rejects, rather than limiting the review artifact to the three stories that happened to qualify on August 16.
- Mark each top-10 item with its editorial decision and whether it passes the unchanged podcast-ready evidence and score gate.
- Preserve candidate URLs, source authority, summaries, editorial decision, rationale, builder actions, caveats, scores, and rank where available.
- Upload the review artifacts from every admitted run, including fail-closed ledgers when collection or editorial review fails.
- Manually dispatch and verify the August 17, 2026 review job after the change passes offline checks.
- Keep public RSS, Pages episode artifacts, GitHub Releases, R2, and NotebookLM unchanged.

## Out of Scope

- Podcast/audio generation, transcription, chapters, RSS items, public site episodes, or R2 uploads during the review period.
- Weakening evidence qualification or treating rejected candidates as podcast-ready stories.
- Enabling `PUBLICATION_ENABLED` or counting review-only jobs toward the seven-shadow publication gate.
- Changing the source roster or editorial model in this task.

## Key Decisions

- The top-10 review is deliberately broader than the future podcast input: it includes accepted and rejected candidates with rationale so the editorial policy can be evaluated holistically.
- Rejected or under-threshold candidates remain visibly non-podcast-ready and do not enter audio generation.
- A completed editorial review is a successful review-only run even when fewer than three candidates are podcast-ready.

## Acceptance Criteria

- [x] An admitted scheduled or manual job collects sources, completes editorial review, writes the full ledger plus a top-10 raw JSON artifact and readable Markdown summary, and returns success without calling NotebookLM or transcription.
- [x] The Markdown and JSON expose matching ranked items with citations and editorial context sufficient for human review.
- [x] No MP3, transcript, chapter, RSS item, manifest, public-site episode, release, R2 object, or NotebookLM temporary source is created by review-only execution.
- [x] Collection/editorial failures remain fail-closed, retain sanitized diagnostic artifacts, and do not enter podcast generation.
- [x] Focused tests prove the top-10 cap, review-only stop boundary, workflow artifact retention, and absence of publication steps.
- [x] A manual August 17 workflow run succeeds and its downloaded artifacts are inspected for item count, fields, citations, and public-state immutability.

## Validation Evidence

- AI Builder Brief commit `38f32ad` is pushed to `origin/main`.
- GitHub Actions run `32055698869` completed successfully with `review-ready` and uploaded artifact `9296370550` containing exactly five files: incoming sources, snapshot, full ledger, review JSON, and review Markdown.
- The review has 10 ranked candidates, 3 podcast-ready accepts, 7 rejects, and 11 cited sources; the full ledger has 36 unique records.
- The run produced no audio, transcript, chapters, manifest, feed, or site artifacts. Its token had `contents: read`, and the job exposed no NotebookLM/R2 credentials or publication steps.
- Pre/post SHA-256 remained `6237752661855669cd6962f2a9d870faf97b708451b566fe12fab726a7959137` for `docs/feed.xml` and `64d1403a00cd3cc9a75a5f699ab989c2c99e4182eb60b8ec0c1472c45983d571` for `docs/index.html`; GitHub releases remain empty and the August 17 R2 MP3 URL remains HTTP 404.
- Offline validation passed: 33 tests, Ruff, mypy, compileall, workflow YAML parsing, and `git diff --check`.
