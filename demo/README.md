# Demo: live Nitan MCP → NotebookLM Markdown

This folder is for **local demo output**. Generated files go to `demo/output/` (gitignored).

## One-command live demo (macOS / Linux)

From the **repository root**:

```bash
./scripts/run_live_demo.sh
```

This:

1. Uses `npx` to run [`@nitansde/mcp`](https://github.com/nitansde/nitan-mcp) with `--python_path` pointing at **this project’s `.venv/bin/python`** (so Cloudflare bypass deps from `requirements.txt` are available).
2. Calls **`discourse_list_top_topics`** with `period=weekly`, `limit=5`.
3. Writes **`demo/output/DEMO_notebooklm_weekly.md`** (NotebookLM-ready 中文素材).
4. Runs **`--publish-notebooklm`**: uploads that Markdown, generates Audio Overview, downloads MP3 to **`releases/weekly_meika_podcast.mp3`** by default — requires **`pip install -r requirements-integrations.txt`**, **`notebooklm login`** (creates `~/.notebooklm/storage_state.json`; **not** the same as Chrome-only Google sign-in), and **`NOTEBOOKLM_NOTEBOOK_ID`** in **`.env`**. See [README.md](../README.md) “Programmatic Audio Overview”.

**Markdown-only (no NotebookLM API):** use the fixture command below without `--publish-notebooklm`, or run `run_pipeline.py` with the same MCP env vars and **omit** `--publish-notebooklm`.

## Fixture-only demo (no forum fetch)

```bash
EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json python run_pipeline.py --skip-briefing --dated
```

## Full pipeline with Gemini briefing

Set `GEMINI_API_KEY` in `.env`, configure MCP as above, then:

```bash
python run_pipeline.py --dated
```

## Reference

- Nitan MCP 介绍帖: https://www.uscardforum.com/t/topic/450599
