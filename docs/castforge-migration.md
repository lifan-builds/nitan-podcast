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

Each show repo owns its own workflow and schedule. CastForge is a framework dependency, not a control plane.

1. `nitan-podcast` triggers its own scheduled workflow.
2. The workflow installs `castforge` as a pip dependency.
3. `run_pipeline.py` wires show-specific hooks into the CastForge pipeline.
4. CastForge executes the pipeline stages using those hooks.
5. The workflow commits and pushes updated artifacts within `nitan-podcast`.
6. GitHub Pages continues serving the feed and MP3s.

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

### Phase 3: Finalize framework dependency

- update `nitan-podcast` workflow to install `castforge` from pip/git
- keep all scheduling and runner config in `nitan-podcast`
- `castforge` remains a pure library with no instance-specific automation

## Initial File Mapping

Move toward `castforge`:

- `briefing_writer.py` (generic Gemini briefing)
- `notebooklm_audio.py` (generic NotebookLM integration)
- `notebooklm_export.py` (generic Markdown export)
- generic pipeline orchestration (now `castforge.pipeline`)

Keep in `nitan-podcast`:

- `run_pipeline.py` (thin wrapper wiring hooks into CastForge)
- `extractor.py`
- `publisher.py`
- `rss_feed.py`
- show-specific RSS defaults and templates
- `.github/workflows/weekly-export.yml` (schedule + runner)
- `scripts/setup_runner.sh`
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
