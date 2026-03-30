# Agent Guide

## Project Overview

**NotebookLM is the key solution for podcast audio.** Python pipeline extracts weekly hot threads from [uscardforum.com](https://uscardforum.com) via **nitan-MCP**, optionally refines with **Gemini**, and exports UTF-8 Markdown. **`--publish-notebooklm`** uploads to NotebookLM, generates Audio Overview, and downloads MP3. Manual UI upload also supported.

Automation runs on a **self-hosted macOS runner** (GitHub Actions) with 3 retry windows on Mondays. `notebooklm login` session required for audio generation.

## Tech Stack

| Layer | Choice |
| ----- | ------ |
| Podcast engine | **Google NotebookLM** (Audio Overview); optional **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** |
| Runtime | Python 3.10+ |
| Forum data | [**Nitan MCP**](https://www.uscardforum.com/t/topic/450599) (`@nitansde/mcp`) |
| Optional LLM | Google Gemini (`google-genai`) — briefing for NotebookLM |
| Audio hosting | GitHub Pages (`docs/episodes/`) — correct `audio/mpeg` MIME |
| RSS | `docs/feed.xml` on GitHub Pages; Apple Podcasts + Spotify listed |

## Project Structure

| Path | Role |
| ---- | ---- |
| `run_pipeline.py` | CLI orchestrator (all flags — see `--help`) |
| `extractor.py` | MCP stdio client; thread detail fetching + selection; `EXTRACTION_FIXTURE_PATH` for tests |
| `briefing_writer.py` | Optional Gemini briefing (`google-genai` SDK) |
| `notebooklm_export.py` | Write UTF-8 `exports/*.md` |
| `notebooklm_audio.py` | `notebooklm-py`: upload → generate → download MP3 |
| `publisher.py` | Episode metadata (rich show notes by category + stats) + forum posts |
| `rss_feed.py` | RSS 2.0 + iTunes; upserts `docs/feed.xml` |
| `docs/episodes/` | MP3 files served by GitHub Pages |
| `scripts/validate_feed.py` | Post-publish feed validator (XML, HTTP content-type, file size) |
| `tests/` | 116 pytest tests (pipeline, publisher, RSS); no network calls |
| `scripts/run_live_demo.sh` | Live MCP → Markdown → `--publish-notebooklm` |
| `.github/workflows/weekly-export.yml` | 6-phase weekly pipeline on self-hosted runner |
| `.env.example` | All env vars documented (authoritative reference) |

## Development Workflow

1. Copy `.env.example` → `.env`; configure MCP + optional `GEMINI_API_KEY` + `NOTEBOOKLM_*`.
2. `python run_pipeline.py` (add `--dated`, `--publish-notebooklm`, `--generate-post`, `--generate-rss` as needed).
3. Tests: `pytest tests/ -v` (offline, <1s). Smoke: `EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json python run_pipeline.py --skip-briefing --dated`.
4. Feed check: `python scripts/validate_feed.py` (local) or `python scripts/validate_feed.py` (live).

## Coding Conventions

- **NotebookLM-first** — Python serves sources, NotebookLM serves audio.
- **UTF-8 everywhere** — `encoding="utf-8"` on all file I/O.
- **Secrets** — env vars only; never commit `.env`.
- **Structured data passthrough** — pass `threads: list[dict]` through the pipeline; avoid regex re-parsing.
- **Lazy imports** — `notebooklm_audio`, `rss_feed` imported only when flags are set.

## Architecture Decisions

- **NotebookLM = audio engine** — single place for spoken 简体中文 output.
- **Audio hosting: GitHub Pages** — serves `audio/mpeg`; Releases kept as backup (serves `application/octet-stream` which broke Apple Podcasts).
- **Podcast tuning** — `NOTEBOOKLM_AUDIO_LENGTH=short` + 7 threads + "点到为止" → ~6 min episodes.
- **Publication** — announcement thread + weekly replies on 美卡论坛; `publisher.py` generates both.
- **Feed validation** — `scripts/validate_feed.py` runs as workflow Phase 6 post-deploy.
- **Programmatic NotebookLM** — `notebooklm-py` behind `--publish-notebooklm`; unofficial API; self-hosted runner only.
- **Thread enrichment** — `discourse_read_topic` fetches OP + replies per thread; `select_threads()` scores + diversifies from larger pool.
- **Distribution** — Apple Podcasts (`id1888784962`) + Spotify (`3jjd0ozToYgW7yje7mfYCg`) via RSS; `PODCAST_PLATFORM_LINKS` env var for forum posts.
