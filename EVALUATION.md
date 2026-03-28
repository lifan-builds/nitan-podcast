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

## Evaluation Log

- 2026-03-26 — **Live demo script** — **Fail** (expected without operator auth): publish step fails with `FileNotFoundError` for `storage_state.json` until `notebooklm login`; Markdown export step succeeds first.
