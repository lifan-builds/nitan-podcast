# AI Builder Brief reliability fix

## Goal

Make the private AI Builder Brief regeneration pipeline complete reliably on the self-hosted Mac while preserving the approved editorial policy, 60-second per-request timeout, NotebookLM quota, public feed, URLs, and GUIDs.

## Background

- Run `31818624847` slept for roughly 44 minutes during editorial review, lost GitHub connectivity, wrote `no-episode-editorial-failure`, and then failed artifact upload with DNS `ENOTFOUND`.
- Run `31823798244` stayed awake and proved the remaining deterministic failure: the single 23-candidate GPT-5.6 Terra review request reached the 60-second application timeout.
- Both runs stopped before NotebookLM, consumed no audio-generation quota, and left public state unchanged.
- The existing client swallows the underlying editorial exception at the pipeline boundary, so the ledger records only a generic status.
- Scheduled attempts are selected from the runner's actual start hour, so a delayed self-hosted job can silently skip its intended attempt window.

## Requirements

1. Keep GPT-5.6 Terra, strict JSON Schema, the usage gate, and a 60-second timeout for each editorial request.
2. Review the bounded candidate pool in deterministic small batches so one response does not need to cover all 24 possible clusters. Merge batches and retain exact one-decision-per-candidate validation.
3. Fail closed if any editorial batch times out, returns invalid JSON, omits or duplicates a candidate, or fails the usage gate. Never continue to NotebookLM after such failure.
4. Persist a sanitized, actionable failure type and stage in the unpublished ledger without credentials, response bodies, or authentication material.
5. Run the episode command under macOS sleep prevention on the self-hosted runner.
6. Select scheduled attempts from their intended schedule slot rather than the delayed runner start time, while preserving the pre-publication one-shadow-per-day behavior and the public 6/8/10 AM Pacific attempts.
7. Keep X optional and non-blocking, `PUBLICATION_ENABLED=false`, the R2 9 GB cap, and all existing public feed identity unchanged.
8. Add focused tests for batching, merged coverage, batch failure, sanitized diagnostics, and schedule-slot selection.
9. Rerun `2026-08-11` privately only after tests pass. Count it only if 3–6 stories, citations, ledger, MP3 duration, transcript, chapters, temporary-source cleanup, and public-state immutability all validate.

## Acceptance Criteria

- [ ] A 23- or 24-candidate editorial pool is split deterministically into bounded batches, each using the strict schema and a 60-second timeout.
- [ ] Merged decisions cover every candidate exactly once; any partial or invalid batch returns `no-episode` before NotebookLM.
- [ ] Editorial failure ledgers identify a safe failure category and batch/stage without secrets or raw model output.
- [ ] The workflow prevents Mac sleep during the episode command.
- [ ] A delayed scheduled job still evaluates the intended 6/8/10 AM Pacific slot correctly; pre-publication mode runs at most one scheduled private shadow per Pacific day.
- [ ] Existing unit and fixture-backed pipeline tests pass with the new focused reliability tests.
- [ ] The private August 11 run either produces a completely validated shadow or fails closed with an attributable reason; no public feed, URL, GUID, or R2 object changes during validation.
- [ ] `PUBLICATION_ENABLED` remains false until seven real shadows pass.

## Out of Scope

- Lowering the three-story editorial threshold or weakening citation/evidence rules.
- Changing the editorial model, adding Sol fallback, or extending the per-request timeout beyond 60 seconds.
- Publishing or replacing public audio before the seven-shadow gate.
- Repairing X authentication, changing the expert panel, or promoting the show.
- Modifying unrelated dirty Trellis framework files in Castforge or Nitan.

