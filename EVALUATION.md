# Evaluation & Contracts

Objective grading criteria and verification contracts for work tracked in [`PLANS.md`](PLANS.md).

## Grading Criteria

- **Functionality:** Pipeline produces UTF-8 Markdown; optional publish uploads + downloads MP3; failures exit non-zero with actionable logs.
- **Code Quality:** Match existing style; lazy optional imports; no secrets in repo.
- **Testing:** 116 offline pytest tests; live MCP + publish verified manually.

## Active Sprint Contracts

### Pytest suite (offline)

- **Verification:** `.venv/bin/python -m pytest tests/ -v`
- **Threshold:** All pass; no network calls; <5s.

### Weekly export (MCP → Markdown)

- **Verification:** `EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json .venv/bin/python run_pipeline.py --skip-briefing --dated` exits `0`.
- **Threshold:** Writes `exports/weekly_meika_*.md`; Chinese not garbled.

### RSS feed playback

- **Verification:** `python scripts/validate_feed.py` (local or live); also workflow Phase 6.
- **Threshold:** 0 errors: XML valid, `enclosure length > 0`, live URL returns `audio/mpeg`, file size matches.

### E2E pipeline (live)

- **Verification:** `.env` configured; `python run_pipeline.py --dated --publish-notebooklm --generate-post --generate-rss`
- **Threshold:** Exit 0; MP3 at `docs/episodes/`; forum reply at `exports/`; feed validator passes.

## Evaluation Log

| Date | Contract | Result | Notes |
|------|----------|--------|-------|
| 2026-03-27 | E2E pipeline | Pass | 7 threads → ~6 min MP3, exit 0 |
| 2026-03-27 | Pytest suite | Pass | 44/44 |
| 2026-03-27 | Forum post | Pass | Separate `_forum_reply.md` |
| 2026-03-28 | Pytest suite | Pass | 91/91 (0.36s) |
| 2026-03-28 | RSS playback | Fail→Fix | `length="0"` → correct size |
| 2026-03-28 | RSS playback | Fail→Fix | Releases `octet-stream` → Pages `audio/mpeg` |
| 2026-03-28 | Feed validator | Pass | 0 errors live |
| 2026-03-29 | Pytest suite | Pass | 116/116 (0.35s) |
| 2026-03-29 | RSS category format | Pass | `<itunes:category text="Technology" />` |
| 2026-03-29 | Thread detail fetch | Pass | Live MCP: OP + replies parsed for 2 threads |
| 2026-03-29 | Platform links env | Pass | `PODCAST_PLATFORM_LINKS` JSON → forum post |
