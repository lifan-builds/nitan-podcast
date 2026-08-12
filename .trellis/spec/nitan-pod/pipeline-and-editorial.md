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
