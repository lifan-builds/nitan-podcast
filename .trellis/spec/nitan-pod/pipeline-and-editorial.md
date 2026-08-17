# Pipeline and Editorial Contracts

## Data flow

Preserve structured `threads: list[dict]` through extraction and publication. Do not regex-reparse rendered text when structured thread data is available. `EXTRACTION_FIXTURE_PATH` is the offline input boundary for deterministic pipeline tests.

Use `encoding="utf-8"` for text file reads and writes. Podcast and source output includes Chinese text, so platform-default encoding is not acceptable.

Keep RSS and CastForge audio imports lazy where the CLI currently defers them. Importing offline commands and test modules must not require optional audio/browser integrations.

## Editorial ordering

An episode contains one or more Story Briefs, each grounded in exactly one forum thread. A Story Brief must establish thread-specific evidence, stakes, caveats, and informative replies before commentary or light banter. Prefer replies that add facts, corrections, constraints, firsthand data, or substantive interpretation; do not elevate usernames, likes, jokes, or reaction-only replies as evidence.

The Source Document owns factual Story Brief structure before any NotebookLM audio style is applied. Category voice guidance is prescriptive and reviewed; it may shape presentation but must not substitute for evidence or mimic forum mood verbatim.

## Integration boundaries

Nitan MCP topic details require the repository parser because `discourse_read_topic` returns formatted text rather than JSON. Test parser changes with captured synthetic fixtures. Do not use live forum calls as routine validation.

## Scenario: Atomic audio publication

### 1. Scope / Trigger

- Applies whenever the scheduled workflow generates or accepts an episode audio asset and then updates Releases, `docs/episodes/`, or `docs/feed.xml`.

### 2. Signatures

- Workflow readiness signal: `steps.release.outputs.audio_url: string`.
- Publication steps: `Generate RSS feed and forum post` → `Commit and push RSS feed` → `Validate live feed`.

### 3. Contracts

- An RSS item may be written only after the current episode has a non-empty audio URL backed by either a downloaded MP3 or the explicit `workflow_dispatch.inputs.audio_url` override.
- An audio-generation failure must fail the job and retain `exports/` as an artifact; it must not create an enclosure with a guessed URL or zero length.
- `docs/feed.xml`, the committed MP3, and the GitHub Release must describe the same episode URL.
- RSS generation must reject a non-positive enclosure length instead of warning and continuing.
- Every committed `docs/episodes/weekly_meika_*.mp3` must have one matching feed enclosure with the same byte length, and every Pages enclosure in the feed must resolve to a committed local MP3.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| NotebookLM fails | Stop release/RSS/commit/validation; upload export; fail job |
| `skip_audio=true`, no override | Export only; do not publish RSS |
| Explicit `audio_url` | Publish using that URL without requiring NotebookLM output |
| Empty release audio URL | Refuse publication before writing RSS |
| Missing MP3 or enclosure length `<= 0` | Raise before feed write; preserve the previous feed |
| Committed weekly MP3 omitted from feed | Offline public-contract test fails |
| Valid released audio | Commit feed and episode, then validate the exact expected URL |

### 5. Good/Base/Bad Cases

- Good: audio downloads, Release returns the Pages URL, and RSS is committed with a positive enclosure length.
- Base: export succeeds but audio is intentionally skipped; the workflow finishes without changing public feed state.
- Bad: continuing after an audio error and allowing the RSS generator to infer a future URL for a nonexistent MP3.

### 6. Tests Required

- Workflow regression tests must assert that audio errors are not ignored, publication steps require a non-empty released audio URL, and exports use `always()` retention.
- RSS/public-contract tests must continue asserting positive enclosure lengths and stable URL/GUID shapes.
- Repository consistency tests must compare committed weekly MP3 filenames and byte lengths to feed enclosures in both directions.

### 7. Wrong vs Correct

```yaml
# Wrong: publishes a placeholder after the provider fails.
continue-on-error: true
if: steps.check.outputs.skip != 'true'

# Correct: fail audio generation and gate every public mutation.
if: steps.release.outputs.audio_url != ''
```

## Scenario: Evidence-gated AI briefing publication

### 1. Scope / Trigger

- Applies to CastForge-powered shows that monitor sources daily but publish only when editorial evidence passes a minimum-story gate.

### 2. Signatures

- `SourceItem.authority`: `primary | independent | analysis | signal`.
- `StoryCluster.kind`: `development | expert_analysis`.
- `SelectionConfig.min_stories: int`.
- `run_episode(...) -> EpisodeManifest | NoEpisodeResult`.

### 3. Contracts

- `analysis` qualifies an attributed expert observation only; technical claims still require a primary artifact or two independent reports.
- Show-owned selection must complete before NotebookLM runs. Fewer than `min_stories` returns `no-episode` without audio or RSS mutation.
- Editorial infrastructure failure is a successful no-publication outcome, not permission to fall back to fixed-score filler.
- Generated MP3 duration is measured from the file and written to the manifest/RSS. Audio beyond the configured ceiling retries once at `short`, then fails closed.
- Public ledgers contain candidate evidence, deterministic rejection or structured review, momentum/recency signals, and selection outcome; secrets and authenticated state never enter artifacts.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| Fewer than minimum qualifying developments | Return `no-episode`; leave RSS unchanged |
| Usage gate, local proxy, or strict schema fails | Retain an unpublished ledger artifact; leave RSS unchanged |
| Optional X source fails | Continue without X; do not weaken factual qualification |
| Audio exceeds ceiling after short retry | Fail before upload/RSS |
| Duration probe fails | Fail before upload/RSS |

### 5. Good/Base/Bad Cases

- Good: three evidence-qualified developments pass structured review, measured audio is within the ceiling, and the ledger/feed publish atomically.
- Base: only two developments qualify; the run records `no-episode` and publishes nothing.
- Bad: publishing routine cloud availability or CI updates because the calendar expects a daily episode.

### 6. Tests Required

- Historical filler rejection, exact strict-schema coverage, weighted thresholds, iterative diversity penalties, and one deep item.
- Analysis-only attribution versus uncorroborated technical claims.
- Optional X failure, collector/proxy/schema failure, minimum-story no-episode behavior, measured signal deltas, duration retry, and feed immutability.

### 7. Wrong vs Correct

```python
# Wrong: narration receives the top fixed-score items even when they are filler.
stories = sorted(candidates, key=score, reverse=True)[:5]

# Correct: deterministic evidence gates and structured editorial review run first.
stories = select_qualified_candidates(candidates)
if len(stories) < config.selection.min_stories:
    return NoEpisodeResult(reason="fewer than minimum qualifying stories")
```

## Scenario: Reliable batched editorial review

### 1. Scope / Trigger

- Applies when a show reviews a bounded candidate pool through CLIProxyAPI.
- Triggered by editorial pools large enough to exceed one model request's practical response time.

### 2. Signatures

- `review_candidates_batched(candidates: list[dict], *, batch_size: int = 6) -> dict`.
- `EditorialReviewError.to_metadata() -> {failure_type: str, stage: str, batch_index?: int}`.

### 3. Contracts

- Preserve candidate input order and slice it into deterministic batches of at most six. Every batch runs the usage gate, GPT-5.6 Terra strict JSON Schema request, and a 60-second request timeout.
- Validate each batch's schema values and exact one-decision-per-candidate coverage before merging. Perform the existing global exact-coverage validation after merging.
- Any usage-gate, timeout, proxy, malformed-response, missing-candidate, duplicate-candidate, or validation failure returns `no-episode` before NotebookLM.
- Unpublished failure ledgers may contain only `failure_type`, `stage`, and a positive one-based `batch_index`; never persist exception text, request headers, response bodies, credentials, cookies, or authenticated URLs.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| 23 or 24 candidates | Split into `6/6/6/5` or `6/6/6/6`; merge in input order |
| One batch times out | Ledger records `timeout`, request stage, and batch index; stop before NotebookLM |
| Batch omits, duplicates, or invents a candidate | Record `invalid_response` at coverage stage; discard all batch results |
| Strict-schema value has wrong type/range | Record `invalid_response`; never coerce it into an accepted decision |
| Usage gate or localhost proxy fails | Record the controlled category/stage without raw details |

### 5. Good/Base/Bad Cases

- Good: four bounded reviews cover 24 candidates exactly once and return controlled decisions for downstream use.
- Base: valid reviews yield fewer than three qualified stories; record `no-episode` without generating audio.
- Bad: send all candidates in one request, inspect the runner's current hour, swallow the timeout, or continue to NotebookLM after partial review.

### 6. Tests Required

- Assert 23- and 24-candidate batch sizes, call order, merged order, and global exact coverage.
- Assert timeout classification, partial/duplicate coverage rejection, strict-schema value validation, failure batch index, and ledger allowlisting without secret substrings.
- Run the complete offline suite before dispatching a live editorial review.

### 7. Wrong vs Correct

```python
# Wrong: one oversized request and a generic, unactionable failure.
response = review_candidates(all_candidates)
except Exception:
    write_ledger(status="no-episode-editorial-failure")

# Correct: bounded requests, exact coverage, and controlled diagnostics.
try:
    response = review_candidates_batched(all_candidates, batch_size=6)
    decisions = validate_review(response, expected_ids, metadata)
except EditorialReviewError as error:
    write_ledger(status="no-episode-editorial-failure", metadata=error.to_metadata())
```

## Scenario: Community-first review-only daily editorial artifacts

### 1. Scope / Trigger

- Applies while AI Builder Brief is in editorial-tuning mode and scheduled/manual jobs must expose a broader candidate set without generating a podcast.
- Triggered by `.github/workflows/daily.yml` or an explicit `ai_builder_brief run --review-only` invocation.

### 2. Signatures

- CLI: `python -m ai_builder_brief run --date YYYY-MM-DD --review-only`.
- Pipeline: `run_daily(..., review_only: bool = False) -> str`; successful review mode returns `review-ready`.
- Collector: `collect_sources(...) -> CollectionResult`; the result contains `items` and a sanitized `x_panel` health record.
- Readiness predicate: `is_podcast_ready(decision: EditorialDecision, sources: Iterable[SourceItem] | None = None) -> bool`.
- JSON artifact: `build/review/YYYY-MM-DD.json`; Markdown artifact: `build/review/YYYY-MM-DD.md`.
- Source health: `build/source-health/YYYY-MM-DD.json` records configured, attempted, successful, in-window, and failed approved X accounts.
- Schedule selector: `python3 scripts/select_schedule_slot.py --cron "0 H * * *" --date YYYY-MM-DD` emits the intended `run`, `shadow`, and `episode_date` outputs; review workflow ignores the legacy `shadow` value.

### 3. Contracts

- Review-only mode shares live collection, snapshot enrichment, deterministic preprocessing, bounded editorial requests, strict value validation, exact candidate coverage, and the full editorial ledger with the episode path.
- X is required for a completed community-first review: at least 80% of the configured approved panel must be queried successfully and at least one X post must fall inside the review window. Failure retains the raw snapshot, source-health artifact, and sanitized ledger, but removes/omits the dated top-ten JSON and Markdown.
- Deterministic admission reserves 12 clusters with X/Hacker News/Hugging Face/measured GitHub community signals and 12 primary-led clusters. Engagement and momentum reach model review as controlled context; they never become authority for technical claims.
- After successful review, select six community-led and four primary-led model-reviewed candidates by editorial score descending and cluster ID ascending. Include accepts and rejects, and allow at most one candidate per organization or explicit product family.
- Explicit product-family identity clusters versioned Ollama, vLLM, llama.cpp, Transformers, and their GitHub counterparts before URL/headline similarity.
- Each JSON candidate contains rank, cluster identity, title, summary, organization, category, publication time, decision, score, `podcast_ready`, full controlled editorial fields, and source IDs/URLs/authorities/summaries. Markdown renders the same ordered records and citations.
- `podcast_ready` is true only for `accept`, score `>= 70`, impact `>= 3`, evidence `>= 3`, and qualifying evidence from a primary source or two independent sources. Signal/analysis-only community observations remain not ready even when accepted.
- Return `review-ready` immediately after writing review artifacts. Do not call `run_episode`, NotebookLM, transcription, R2, RSS, manifests, public-site rendering, or `docs/` mutation.
- The scheduled workflow admits only the intended 6 AM Pacific slot across PDT/PST, wraps the review command with `caffeinate`, has `contents: read`, installs no transcription extra, exposes only `episode_date`, and contains no audio/R2 secrets, public validation, commit, or push steps.
- Collector/editorial failures retain only the sanitized fail-closed ledger; never emit a partial top ten.

### 4. Validation & Error Matrix

| Condition | Required behavior |
| --- | --- |
| 12 valid reviewed candidates | Emit ranks 1–10 only; deterministic tie-break by cluster ID |
| High-scoring editorial reject | Include in top ten with `podcast_ready: false` and rationale |
| Fewer than three ready candidates | Return `review-ready`; show the actual ready count |
| Collector or editorial failure | Return `no-episode`; retain sanitized ledger; omit partial review files |
| Fewer than 80% of X accounts succeed or zero in-window X posts | Return `no-episode`; retain raw snapshot/source health; emit no top ten |
| Multiple release versions from one product | Collapse under one explicit product-family cluster |
| One organization/product would occupy multiple review slots | Keep its highest-ranked eligible item only and expose any mix shortfall |
| Existing RSS GUID for the date | Still run review-only mode; published-date skipping applies only to episode mode |
| 6 AM cron starts late | Use the intended cron slot/date rather than runner wall-clock hour |
| Non-6 AM cron during review period | Skip without collection or artifact generation |

### 5. Good/Base/Bad Cases

- Good: healthy X coverage yields six distinct community-led themes and four distinct primary developments with matching citations and no audio side effects.
- Base: healthy collection has too few distinct candidates for one class; render fewer than ten and expose the exact mix shortfall.
- Bad: silently complete a release-only top ten after X fails, treat likes as factual corroboration, or fill a diversity shortfall with duplicate Ollama/OpenAI entries.

### 6. Tests Required

- Assert X retry/engagement/health, the 80% plus in-window gate, product-family clustering, 12/12 admission, 6/4 selection, one-per-organization/product diversity, signal-only readiness failure, JSON/Markdown parity, citations, and UTF-8 output.
- Monkeypatch `run_episode` to fail if called and assert review-only execution still returns `review-ready` with no feed, manifest, audio, transcript, chapter, site, or `docs/` artifacts.
- Workflow tests assert `--review-only`, `contents: read`, artifact retention, explicit manual date handling, individual PDT/PST cron entries, and absence of NotebookLM/R2 credentials, `PUBLICATION_ENABLED`, shadow input, public validation, commit, and push steps.

### 7. Wrong vs Correct

```python
# Wrong: silently produce a release-centric review after social collection fails.
items = collect_sources(config, start=start, end=end)
write_review_artifacts(review_date, top_fixed_scores(items))

# Correct: preserve diagnostics and fail closed until the approved panel is healthy.
result = collect_sources(config, start=start, end=end)
write_source_health(review_date, result.x_panel)
if review_only and not result.healthy:
    write_ledger(status="no-review-source-failure")
    return "no-episode"
```
