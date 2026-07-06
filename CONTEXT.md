# Nitan Podcast
<!-- context-harness:schema v3 -->

Nitan Podcast turns USCardForum discussions into short Chinese podcast episodes for listeners who want the week’s important forum context without reading every thread.

## Project

Nitan Podcast turns USCardForum discussions into short Chinese podcast episodes. This show repo owns identity, RSS, published assets, GitHub Pages hosting, and GitHub Actions scheduling; reusable pipeline stages live in CastForge.

## Structure

- `run_pipeline.py` is the thin CLI that wires show hooks into `castforge.pipeline`.
- `extractor.py` fetches forum data through nitan-MCP and selects/enriches threads.
- `publisher.py` creates episode metadata and forum post/reply Markdown.
- `rss_feed.py` writes the public podcast RSS feed under `docs/feed.xml`.
- `.github/workflows/weekly-export.yml` runs the scheduled self-hosted macOS automation.
- `docs/episodes/` holds GitHub Pages-served MP3 episode assets.
- `tests/` contains offline pytest coverage for pipeline, publisher, RSS, and public contracts.

## Operating Constraints

- NotebookLM is the audio engine; Python prepares sources and publication artifacts.
- Preserve the subscriber contract in `public_contract.py` and `tests/test_public_contract.py`.
- Use UTF-8 for file I/O.
- Keep secrets in environment variables only; never commit `.env`.
- Preserve structured `threads: list[dict]` data through the pipeline instead of regex re-parsing when available.
- Keep RSS and CastForge audio imports lazy where the CLI already does.

## Workflow

- Local setup: copy `.env.example` to `.env`, configure MCP, optional Gemini, and NotebookLM variables.
- CastForge is expected from a sibling `../castforge` checkout or `pip install -e ../castforge`.
- Main run: `python run_pipeline.py`, with flags such as `--dated`, `--publish-notebooklm`, `--generate-post`, and `--generate-rss`.
- Offline tests: `pytest tests/ -v`.
- Fixture smoke: `EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json python run_pipeline.py --skip-briefing --dated`.
- Feed validation: `python scripts/validate_feed.py`.

## Language

**Story Brief**:
A source-grounded mini-brief for one forum thread that establishes facts, stakes, representative replies, caveats, and only then a podcast angle.
_Avoid_: AI riff, title summary, hot-take segment

**Source Document**:
The NotebookLM-facing Markdown that carries canonical **Story Briefs** for an episode.
_Avoid_: raw dump, prompt-only guidance

**Category Voice Guide**:
A prescriptive editorial guide that defines how Nitan Podcast should handle each forum category.
_Avoid_: tone mimicry, weekly style scrape, forum cosplay

**Evidence From Source**:
Thread-specific facts, claims, numbers, dates, constraints, and replies that the podcast may rely on.
_Avoid_: inferred background, host guess, unsupported explanation

**Informative Reply**:
A forum response that adds facts, firsthand data points, corrections, constraints, or substantive interpretation.
_Avoid_: troll reply, pure joke, reaction-only comment, metadata

## Relationships
- `AGENTS.md` is the small activation layer; `CONTEXT.md` is the durable source of truth, indexed by `scripts/context-index.js`.

- An **Episode** contains one or more **Story Briefs**.
- A **Story Brief** is based on exactly one forum thread.
- A **Story Brief** treats commentary as secondary to factual setup.
- A **Story Brief** must establish **Evidence From Source** before interpreting community reaction.
- **Evidence From Source** prioritizes **Informative Replies** over usernames, likes, or low-information reactions.
- A **Source Document** owns the factual structure of each **Story Brief** before any audio style is applied.
- A **Category Voice Guide** informs **Story Briefs** without copying the forum's mood verbatim.

## Example Dialogue

> **Dev:** "Should the hosts open a thread segment with jokes from the replies?"
> **Domain expert:** "No. First make the **Story Brief** clear enough for someone who never opened the thread, then use replies for color and disagreement."

## Flagged Ambiguities

- "Review feedback" identified a conflict between factual digest and commentary-first entertainment; resolved: the default episode promise is source-grounded **Story Briefs** with light banter.
- Factual grounding belongs in the **Source Document**, not only in Gemini or NotebookLM prompting.
- Category tone is prescriptive: Nitan can inform the **Category Voice Guide**, but the show owns the editorial voice.
- The **Category Voice Guide** is a reviewed show artifact, not an environment-only prompt tweak.
- A **Source Document** includes the default voice once and injects only the relevant category note for each **Story Brief**.
- Reply handling should optimize for information density, not forum color: fetch deeper and filter out troll or reaction-only replies where possible.
- **Informative Replies** are identified with deterministic information-density signals before introducing an LLM classifier.
- **Informative Reply** filtering belongs in the Nitan extraction layer, before Gemini or NotebookLM sees the source.

## Learned Patterns

- GitHub Pages serves MP3 assets with the correct `audio/mpeg` MIME type; GitHub Releases served assets as `application/octet-stream` and broke Apple Podcasts ingestion.
- NotebookLM length is controlled by `NOTEBOOKLM_AUDIO_LENGTH` plus thread count more reliably than natural-language duration instructions.
- `notebooklm login` creates Playwright storage under `~/.notebooklm/storage_state.json`; a normal Chrome sign-in is not enough for automation.
- nitan-MCP `discourse_read_topic` returns formatted text, not JSON, so topic detail parsing needs the custom parser in `extractor.py`.

## Imported Agent Notes
<!-- Migrated from the pre-v3 AGENTS.md during the one-time context-harness upgrade. Keep durable facts here; keep AGENTS.md small. -->

# Agent Guide
<!-- context-harness:schema v3 -->

## Context Contract
- At session start/resume, read `NOW.md` first, then use the Context Index
  below to choose relevant `CONTEXT.md` sections.
- Before planning or editing, respect `CONTEXT.md` `## Rules`.
- If the user teaches a durable term, invariant, workflow, constraint, or
  correction, update `CONTEXT.md` before it scrolls away.
- Route task-local findings and decisions to `PLAN.md`; durable lessons to
  `CONTEXT.md`.
- After updating `CONTEXT.md`, run `node scripts/context-index.js update`.
- Before ending, update `NOW.md` with current focus, blockers, next step, and
  touched files.

## Context Index

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
