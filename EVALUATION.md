# Evaluation & Contracts

Objective grading criteria and verification contracts for work tracked in [`PLANS.md`](PLANS.md).

## Grading Criteria

- **Functionality:** Pipeline produces UTF-8 NotebookLM-ready Markdown; optional publish uploads MD, generates Audio Overview, downloads MP3; failures exit non-zero with actionable logs.
- **Code Quality:** Match existing style; lazy optional imports for `notebooklm`; no secrets in repo.
- **Testing:** Smoke via `EXTRACTION_FIXTURE_PATH` + `--skip-briefing`; live MCP + publish verified manually after `notebooklm login`.

## Active Sprint Contracts

### Weekly export (MCP → Markdown)

- **Verification Method:** `EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json .venv/bin/python run_pipeline.py --skip-briefing --dated` exits `0`; writes `exports/weekly_meika_*.md` or configured path.
- **Acceptance Threshold:** Markdown contains expected structure; Chinese copy not garbled.

### Live demo script

- **Verification Method:** From repo root, `.venv` + `requirements.txt` installed, network available: `./scripts/run_live_demo.sh`.
- **Acceptance Threshold:** Exit `0` only when `NOTEBOOKLM_NOTEBOOK_ID` is set (e.g. in `.env`), `requirements-integrations.txt` installed, and `~/.notebooklm/storage_state.json` exists after **`notebooklm login`**. Writes `demo/output/DEMO_notebooklm_weekly.md` and `releases/weekly_meika_podcast.mp3` (or override via `--notebooklm-audio-out` if invoked via `run_pipeline.py` directly).

### Programmatic NotebookLM publish

- **Verification Method:** Same as live demo publish path, or `run_pipeline.py ... --publish-notebooklm` with valid env.
- **Acceptance Threshold:** MP3 present at logged path; NotebookLM notebook shows new source.

### Pytest suite (offline)

- **Verification Method:** `cd /path/to/nitan-podcast && .venv/bin/python -m pytest tests/ -v`
- **Acceptance Threshold:** All tests pass; no network calls; completes in <5s.

### Forum post generation

- **Verification Method:** `python run_pipeline.py --skip-briefing --dated --generate-post` with fixture or live MCP.
- **Acceptance Threshold:** Produces `exports/*_forum_reply.md` (or `_forum_post.md`) with topic table, stats columns, and audio link placeholder. Does **not** overwrite the NotebookLM source file.

### E2E pipeline (live)

- **Verification Method:** `.env` configured with MCP + NotebookLM; `python run_pipeline.py --skip-briefing --dated --publish-notebooklm --generate-post`
- **Acceptance Threshold:** Exit 0; MP3 at `releases/weekly_meika_YYYY-Www.mp3` (~5-8 min); forum reply at `exports/`; NotebookLM notebook shows new source.

### RSS feed playback

- **Verification Method:** Fetch `https://lifan-builds.github.io/nitan-podcast/feed.xml`; check `<enclosure>` has `length > 0` and valid URL.
- **Acceptance Threshold:** Apple Podcasts / other players can stream the episode. Enclosure length must reflect actual MP3 file size.

## Evaluation Log

- 2026-03-26 — **Live demo script** — **Fail** (expected without operator auth): publish step fails with `FileNotFoundError` for `storage_state.json` until `notebooklm login`; Markdown export step succeeds first.
- 2026-03-27 — **E2E pipeline (live)** — **Pass**: MCP extraction (7 threads, weekly) → Gemini briefing → NotebookLM Audio Overview (short, ~6 min) → MP3 downloaded (~20MB). Exit 0. Forum reply generated with topic table.
- 2026-03-27 — **Pytest suite** — **Pass**: 44/44 tests pass in 0.35s; no network calls.
- 2026-03-27 — **Forum post generation** — **Pass**: `write_forum_post()` produces separate `_forum_reply.md` file; filename collision bug fixed.
- 2026-03-28 — **Pytest suite** — **Pass**: 91/91 tests pass in 0.35s (added publisher tests + conftest + --markdown-input test).
- 2026-03-28 — **RSS feed playback** — **Fail → Fix**: `enclosure length="0"` broke Apple Podcasts. Fixed: correct URL + `length="10768793"`. Verified live feed has correct values.
