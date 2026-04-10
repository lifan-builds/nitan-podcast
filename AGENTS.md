# Agent Guide

## Project Overview

**NotebookLM is the key solution for podcast audio.** Python pipeline extracts weekly hot threads from [uscardforum.com](https://uscardforum.com) via **nitan-MCP**, optionally refines with **Gemini**, and exports UTF-8 Markdown. **`--publish-notebooklm`** uploads to NotebookLM, generates Audio Overview, and downloads MP3. Manual UI upload also supported.

This repository is the **Nitan Podcast show repo**: it owns identity, RSS, published assets, and GitHub Actions scheduling. Reusable pipeline stages live in **[CastForge](https://github.com/lifan-builds/castforge)** and are installed as a dependency (see `.github/workflows/weekly-export.yml`).

Automation runs on a **self-hosted macOS runner** (GitHub Actions) with 3 retry windows on Mondays. `notebooklm login` session required for audio generation.

## Tech Stack

| Layer | Choice |
| ----- | ------ |
| Pipeline framework | **[CastForge](https://github.com/lifan-builds/castforge)** — orchestration, briefing, export, NotebookLM helpers |
| Podcast engine | **Google NotebookLM** (Audio Overview); optional **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** |
| Runtime | Python 3.10+ |
| Forum data | [**Nitan MCP**](https://www.uscardforum.com/t/topic/450599) (`@nitansde/mcp`) |
| Optional LLM | Google Gemini (`google-genai`) — briefing for NotebookLM |
| Audio hosting | GitHub Pages (`docs/episodes/`) — correct `audio/mpeg` MIME |
| RSS | `docs/feed.xml` on GitHub Pages; Apple Podcasts + Spotify listed |

## Project Structure

| Path | Role |
| ---- | ---- |
| `run_pipeline.py` | Thin CLI: wires show hooks into `castforge.pipeline` |
| `_castforge.py` | Resolves CastForge import (sibling checkout or venv install) |
| `public_contract.py` | Stable public feed/episode URLs and GUID prefix — do not break subscribers |
| `podcast.yaml` | Instance contract for CastForge consumers |
| `extractor.py` | MCP stdio client; thread detail fetching + selection; `EXTRACTION_FIXTURE_PATH` for tests |
| `briefing_writer.py` | Compatibility re-export of CastForge Gemini briefing |
| `notebooklm_export.py` | Compatibility re-export of CastForge Markdown export |
| `notebooklm_audio.py` | Compatibility re-export of CastForge NotebookLM audio |
| `publisher.py` | Episode metadata (rich show notes by category + stats) + forum posts |
| `rss_feed.py` | RSS 2.0 + iTunes; upserts `docs/feed.xml` |
| `docs/episodes/` | MP3 files served by GitHub Pages |
| `scripts/validate_feed.py` | Post-publish feed validator (XML, HTTP content-type, file size) |
| `tests/` | pytest (pipeline, publisher, RSS, public contract); no network calls |
| `scripts/run_live_demo.sh` | Live MCP → Markdown → `--publish-notebooklm` |
| `.github/workflows/weekly-export.yml` | Scheduled + manual weekly pipeline; installs CastForge then runs `run_pipeline.py` |
| `.env.example` | All env vars documented (authoritative reference) |
| `docs/castforge-migration.md` | Repo split and execution model |

## Development Workflow

1. Copy `.env.example` → `.env`; configure MCP + optional `GEMINI_API_KEY` + `NOTEBOOKLM_*`.
2. For local dev without a pip-installed CastForge, keep a sibling checkout at `../castforge` or install with `pip install -e ../castforge`.
3. `python run_pipeline.py` (add `--dated`, `--publish-notebooklm`, `--generate-post`, `--generate-rss` as needed).
4. Tests: `pytest tests/ -v` (offline, sub-second). Smoke: `EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json python run_pipeline.py --skip-briefing --dated`.
5. Feed check: `python scripts/validate_feed.py` (local) or live URL.

## Coding Conventions

- **NotebookLM-first** — Python serves sources, NotebookLM serves audio.
- **UTF-8 everywhere** — `encoding="utf-8"` on all file I/O.
- **Secrets** — env vars only; never commit `.env`.
- **Structured data passthrough** — pass `threads: list[dict]` through the pipeline; avoid regex re-parsing when threads are available.
- **Lazy imports** — `rss_feed` and CastForge audio path stay lazy where the CLI already did; compatibility modules import CastForge on load (lightweight).

## Architecture Decisions

- **CastForge = framework** — show repos own schedule, runner, secrets, and published URLs; CastForge provides reusable stages.
- **NotebookLM = audio engine** — single place for spoken 简体中文 output.
- **Audio hosting: GitHub Pages** — serves `audio/mpeg`; Releases kept as backup (serves `application/octet-stream` which broke Apple Podcasts).
- **Podcast tuning** — `NOTEBOOKLM_AUDIO_LENGTH=short` + 7 threads + "点到为止" → ~6 min episodes.
- **Publication** — announcement thread + weekly replies on 美卡论坛; `publisher.py` generates both.
- **Feed validation** — `scripts/validate_feed.py` runs as workflow Phase 6 post-deploy.
- **Programmatic NotebookLM** — `notebooklm-py` behind `--publish-notebooklm`; unofficial API; self-hosted runner only.
- **Thread enrichment** — `discourse_read_topic` fetches OP + replies per thread; `select_threads()` scores + diversifies from larger pool.
- **Distribution** — Apple Podcasts (`id1888784962`) + Spotify (`3jjd0ozToYgW7yje7mfYCg`) via RSS; `PODCAST_PLATFORM_LINKS` env var for forum posts.
- **Subscriber contract** — `public_contract.py` + `tests/test_public_contract.py` lock feed URL, episode URL pattern, and GUID prefix.
