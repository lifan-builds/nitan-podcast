# CastForge Migration

This document describes the planned split between the reusable framework repo, `castforge`, and the public show repo, `nitan-podcast`.

## Goal

Separate reusable podcast automation from show-specific identity without breaking the public podcast feed.

## Repository Roles

### `castforge`

Owns:

- pipeline orchestration
- scheduling and retry logic
- self-hosted runner setup
- shared integrations such as Gemini and NotebookLM
- reusable artifact and manifest contracts

### `nitan-podcast`

Owns:

- Nitan MCP extraction behavior
- thread selection rules
- prompts, editorial rules, and forum templates
- public assets and metadata
- `docs/feed.xml`
- `docs/episodes/*.mp3`

## Non-Breaking Contract

The migration must preserve all subscriber-visible endpoints.

- Keep `https://lifan-builds.github.io/nitan-podcast/feed.xml`
- Keep `https://lifan-builds.github.io/nitan-podcast/`
- Keep `https://lifan-builds.github.io/nitan-podcast/episodes/weekly_meika_YYYY-Www.mp3`
- Keep episode GUIDs in the `nitan-podcast-YYYY-Www` format
- Keep historical files under `docs/episodes/`

If those values drift, Spotify and Apple Podcasts may treat the show as broken or new.

## Execution Model

The target operating model is:

1. `castforge` runs the scheduled job.
2. The workflow checks out both repos.
3. `castforge` reads `nitan-podcast/podcast.yaml`.
4. `castforge` executes the pipeline using the show repo's adapters and templates.
5. Outputs are written back into the `nitan-podcast` worktree.
6. `nitan-podcast` is committed and pushed so GitHub Pages continues serving the feed and MP3s.

## Migration Sequence

### Phase 1: Stabilize contracts in `nitan-podcast`

- centralize public URLs and GUID prefixes in `public_contract.py`
- document the instance contract in `podcast.yaml`
- add tests that lock feed URL, GUID, and episode URL conventions

### Phase 2: Extract framework into `castforge`

- move generic pipeline stages
- move workflow orchestration and runner setup
- move integration wrappers for Gemini and NotebookLM
- define a run manifest and artifact contract

### Phase 3: Switch automation ownership

- move the weekly scheduler to `castforge`
- grant `castforge` permission to push changes into `nitan-podcast`
- keep `nitan-podcast` as the public publishing repo

## Initial File Mapping

Move toward `castforge`:

- `run_pipeline.py`
- `briefing_writer.py`
- `notebooklm_audio.py`
- `notebooklm_export.py`
- reusable parts of `rss_feed.py`
- `.github/workflows/weekly-export.yml`
- `scripts/setup_runner.sh`

Keep in `nitan-podcast`:

- `extractor.py`
- `publisher.py`
- show-specific RSS defaults and templates
- `docs/feed.xml`
- `docs/episodes/`
- `assets/`

## Validation Checklist

Run this before and after switching automation:

1. `pytest tests/ -v`
2. `python scripts/validate_feed.py --local-only docs/feed.xml`
3. Verify existing `<guid>` values are unchanged
4. Verify old MP3 files still exist in `docs/episodes/`
5. Verify new feed items still point to `audio/mpeg` assets on GitHub Pages
