# Agent Guide

## Project Overview

**NotebookLM is the key solution for podcast audio.** This project’s job is to **feed NotebookLM high-quality sources**: weekly **key information** from [uscardforum.com](https://uscardforum.com) via **nitan-MCP**, optionally refined into Chinese **Markdown** by **Google Gemini**, then **exported** as UTF-8 files for upload. **Audio Overview** (or equivalent) runs **inside Google NotebookLM** on those sources — not via custom TTS, ElevenLabs, Azure Speech, or pydub.

**Python pipeline role:** extract → (optional) brief → **export Markdown** → optionally **`--publish-notebooklm`** ([`notebooklm_audio.py`](notebooklm_audio.py) + **`notebooklm-py`**) to upload, generate Audio Overview, and save **MP3** under `releases/`. **NotebookLM role:** same product for audio; manual UI upload remains supported.

Automation: **cron** / **GitHub Actions** for export is straightforward; **`--publish-notebooklm`** needs **`notebooklm login`** session storage — treat as **local or self-hosted** by default (see README).

## Tech Stack

| Layer | Choice |
| ----- | ------ |
| **Podcast engine** | **Google NotebookLM** (Audio Overview); optional **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** for unofficial programmatic upload/generate/download — see `FINDINGS.md` |
| Runtime | Python 3.10+ |
| Forum data | [**Nitan MCP**](https://www.uscardforum.com/t/topic/450599) (`@nitansde/mcp`, [repo](https://github.com/nitansde/nitan-mcp)) → uscardforum.com |
| Optional LLM | Google Gemini API — compress/format extraction into a single Chinese **Markdown** source for NotebookLM |
| Optional automation | Playwright driving the NotebookLM **web UI** (unofficial; see `FINDINGS.md`) |
| Scheduling | cron / GHA for **extract → export**; **`--publish-notebooklm`** usually **not** on vanilla GHA |

## Project Structure

| Path | Role |
| ---- | ---- |
| `run_pipeline.py` | **CLI orchestrator**: `--publish-notebooklm`, `--notebooklm-audio-out`, `--dated`, `--skip-briefing`, `--list-mcp-tools`, `--generate-post`, `--audio-url` |
| `extractor.py` | MCP stdio client; `MCP_*` env; `EXTRACTION_FIXTURE_PATH` for tests; `threads_to_source_markdown` |
| `briefing_writer.py` | Optional Gemini: raw extraction → dense Chinese **Markdown** for NotebookLM |
| `notebooklm_export.py` | Write UTF-8 `exports/*.md` |
| `notebooklm_audio.py` | Optional **`notebooklm-py`**: `add_file` → `generate_audio` → `wait` → `download_audio` |
| `publisher.py` | Episode metadata (中文 title, topic bullets) + 美卡论坛 Discourse post generator |
| `fixtures/sample_extraction.json` | Sample threads JSON for CI / local dry run |
| `tests/test_pipeline.py` | pytest suite (44 tests): extractor, export, briefing, CLI args, integration smoke |
| `scripts/run_live_demo.sh` | Live **`discourse_list_top_topics`** (weekly, limit 5) → `demo/output/DEMO_notebooklm_weekly.md` → **`--publish-notebooklm`** (needs `.env` **`NOTEBOOKLM_*`** + **`notebooklm login`**; not Chrome-only sign-in) |
| `demo/README.md` | Demo runbook |
| `.github/workflows/weekly-export.yml` | Scheduled workflow + artifact upload |
| `requirements.txt` | MCP, `google-generativeai`, `python-dotenv`, Cloudflare deps for Nitan |
| `requirements-integrations.txt` | Optional **`notebooklm-py[browser]`** (programmatic NotebookLM) |
| `.env.example` | All configurable env vars documented |
| `AGENTS.md` | This file |
| `PLANS.md` | Living ExecPlan (NotebookLM-first) |
| `FINDINGS.md` | NotebookLM API status, UI-automation notes, error log |
| `README.md` | Runbook, NotebookLM + **publication** checklists, cron/GHA |
| `EVALUATION.md` | Verification contracts and evaluation log |

## Environment variables (reference)

| Variable | Required | Purpose |
| -------- | -------- | ------- |
| `MCP_SERVER_COMMAND` | Yes (unless fixture) | Stdio MCP server executable |
| `MCP_SERVER_ARGS` | No | JSON array of extra argv |
| `MCP_EXTRACT_TOOL` | Yes (unless fixture) | `tools/call` name for weekly digest |
| `MCP_EXTRACT_TOOL_ARGUMENTS` | No | JSON object; default `{}` |
| `MCP_SERVER_ENV_JSON` | No | Extra env merged into server process |
| `EXTRACTION_FIXTURE_PATH` | No | JSON file → skip MCP (demo/CI) |
| `GEMINI_API_KEY` | If briefing enabled | Gemini API |
| `GEMINI_MODEL` | No | Default `gemini-2.0-flash` |
| `NOTEBOOKLM_NOTEBOOK_ID` | Yes if `--publish-notebooklm` | Target notebook |
| `NOTEBOOKLM_AUDIO_LANGUAGE` | No | Default `zh` |
| `NOTEBOOKLM_AUDIO_INSTRUCTIONS` | No | Default 中文 instructions in code |
| `NOTEBOOKLM_AUDIO_FORMAT` / `NOTEBOOKLM_AUDIO_LENGTH` | No | `deep_dive`/`brief`/…, `short`/`default`/`long` |
| `NOTEBOOKLM_GENERATION_TIMEOUT` | No | Seconds (default 600) |
| `NOTEBOOKLM_SOURCE_WAIT_TIMEOUT` | No | Source indexing wait (default 180) |
| `NOTEBOOKLM_STORAGE_PATH` | No | Override `storage_state.json` path |
| `NOTEBOOKLM_HTTP_TIMEOUT` | No | HTTP client timeout (default 60) |

## Development Workflow

1. `.env` — MCP + tool; `GEMINI_API_KEY` unless `--skip-briefing`; `NOTEBOOKLM_*` if publishing.
2. `python run_pipeline.py` (add `--dated`, `--publish-notebooklm` as needed).
3. **Manual path:** upload `exports/*.md` → **中文** Audio Overview in UI.
4. **UTF-8** for all file I/O.

**Testing:** `EXTRACTION_FIXTURE_PATH=...` + `--skip-briefing` for MCP-free smoke; full publish requires **`notebooklm login`** (creates `~/.notebooklm/storage_state.json`) + **`NOTEBOOKLM_NOTEBOOK_ID`** — signing into Google in normal Chrome does **not** satisfy the CLI.

**Docs set:** Maintain **`AGENTS.md`**, **`PLANS.md`**, **`FINDINGS.md`**, **`EVALUATION.md`**, **`README.md`** together when behavior or ops change (context-harness).

## Coding Conventions

- **NotebookLM-first** — Python serves **sources**, NotebookLM serves **audio**.
- **UTF-8 everywhere** — `encoding="utf-8"` on reads/writes.
- **Secrets** — environment variables only; never commit `.env`.
- **MCP** — `mcp` package stdio client; tool contract is **server-defined** — normalize results in `tool_result_to_threads`.

## Architecture Decisions

- **Designated podcast engine: NotebookLM** — Single place for spoken output.
- **Extraction = key information** — `list[dict]` → Markdown sources; **简体中文** podcast enforced via NotebookLM instructions + Chinese sources.
- **Optional Gemini briefing** — Improves NotebookLM grounding vs. raw key-value dumps.
- **Weekly jobs** — `run_pipeline.py` is headless with non-zero exit on failure.
- **Programmatic NotebookLM** — **`notebooklm-py`** behind `--publish-notebooklm`; unofficial API; pin `requirements-integrations.txt`.
- **UI automation** — DIY Playwright non-core; see `FINDINGS.md`.
