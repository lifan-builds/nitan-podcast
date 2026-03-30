# Nitan Podcast — 美卡论坛 (USCardForum) 每周AI播客

**论坛帖：[【Nitan Podcast】你的每周美卡论坛精华播客](https://www.uscardforum.com/t/topic/494521)**

Python 3.10+ pipeline that extracts weekly hot threads from [uscardforum.com](https://uscardforum.com) via [**Nitan MCP**](https://www.uscardforum.com/t/topic/450599), optionally refines with **Gemini**, and feeds **Google NotebookLM** to generate a ~6 min 简体中文 podcast.

```mermaid
flowchart LR
  E[Extract via MCP] --> B[Optional Gemini brief]
  B --> X[Export Markdown]
  X --> NLM[NotebookLM Audio]
  NLM --> MP3[GitHub Pages MP3]
  MP3 --> RSS[Apple / Spotify / RSS]
```

## Quick Start

```bash
git clone https://github.com/lifan-builds/nitan-podcast.git
cd nitan-podcast
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Configure MCP_*, optional GEMINI_API_KEY, NOTEBOOKLM_*
```

## Run the Pipeline

```bash
python run_pipeline.py --dated                          # MCP → Gemini → Markdown
python run_pipeline.py --dated --skip-briefing          # Skip Gemini
python run_pipeline.py --dated --publish-notebooklm     # + NotebookLM audio
python run_pipeline.py --dated --generate-post --generate-rss --audio-url "https://..."

# Dry run (no MCP needed)
EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json python run_pipeline.py --skip-briefing --dated
```

Stdout prints the output file path. See `python run_pipeline.py --help` for all flags.

## Subscribe

| Platform | Link |
| -------- | ---- |
| **Apple Podcasts** | [Nitan Podcast](https://podcasts.apple.com/us/podcast/nitan-podcast/id1888784962) |
| **Spotify** | [Nitan Podcast](https://open.spotify.com/show/3jjd0ozToYgW7yje7mfYCg) |
| **RSS** | `https://lifan-builds.github.io/nitan-podcast/feed.xml` |
| **美卡论坛** | [announcement thread](https://www.uscardforum.com/t/topic/494521) |

## GitHub Actions (Automated Weekly Pipeline)

Runs on a **self-hosted macOS runner** (`nitan-mac`). Schedule: 3 retry windows every Monday (6 AM / 12 PM / 6 PM PST). First success publishes; subsequent triggers skip.

**Pipeline phases:**

1. MCP extract → Gemini briefing → export Markdown
2. NotebookLM → Audio Overview → MP3
3. GitHub Release (backup) + copy MP3 to `docs/episodes/`
4. Generate RSS feed + forum post draft
5. Commit + push (GitHub Pages auto-deploys)
6. Validate live feed (`scripts/validate_feed.py`)

**Manual trigger:** Actions → `weekly-podcast` → Run workflow.

**Only manual step:** Post `exports/*_forum_reply.md` as a reply to the [announcement thread](https://www.uscardforum.com/t/topic/494521).

## NotebookLM Setup

For `--publish-notebooklm` (programmatic audio via [notebooklm-py](https://github.com/teng-lin/notebooklm-py)):

1. `pip install -r requirements-integrations.txt && playwright install chromium`
2. `notebooklm login` (stores `~/.notebooklm/storage_state.json` — **not** the same as Chrome Google sign-in)
3. Set `NOTEBOOKLM_NOTEBOOK_ID` in `.env`

Tune via env: `NOTEBOOKLM_AUDIO_LENGTH` (`short`/`default`/`long`), `NOTEBOOKLM_AUDIO_FORMAT`, `NOTEBOOKLM_AUDIO_INSTRUCTIONS` — see [`.env.example`](.env.example).

**Manual path:** Upload `exports/*.md` to NotebookLM UI → set 中文 instructions → generate Audio Overview.

## Environment

All env vars documented in [`.env.example`](.env.example). Key ones:

- `MCP_SERVER_COMMAND` / `MCP_SERVER_ARGS` / `MCP_EXTRACT_TOOL` — Nitan MCP config
- `GEMINI_API_KEY` — optional, for briefing
- `NOTEBOOKLM_NOTEBOOK_ID` — required for `--publish-notebooklm`

## Development

```bash
pytest tests/ -v              # 91 tests, offline, <1s
python scripts/validate_feed.py   # Check RSS feed (local or live)
```

Project docs: [`AGENTS.md`](AGENTS.md) (architecture), [`PLANS.md`](PLANS.md) (plan), [`FINDINGS.md`](FINDINGS.md) (research), [`EVALUATION.md`](EVALUATION.md) (contracts).

## Project Structure

| File | Purpose |
| ---- | ------- |
| `run_pipeline.py` | CLI orchestrator |
| `extractor.py` | MCP client + fixture support |
| `briefing_writer.py` | Optional Gemini briefing |
| `notebooklm_export.py` | UTF-8 Markdown export |
| `notebooklm_audio.py` | NotebookLM upload/generate/download |
| `publisher.py` | Episode metadata + forum posts |
| `rss_feed.py` | RSS 2.0 + iTunes feed generator |
| `docs/episodes/` | MP3s served by GitHub Pages (`audio/mpeg`) |
| `scripts/validate_feed.py` | Post-publish feed validator |
| `scripts/run_live_demo.sh` | Live demo script |
| `scripts/setup_runner.sh` | Runner prerequisite checker |
| `tests/` | 91 pytest tests (pipeline, publisher, RSS) |

## License

MIT
