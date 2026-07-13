# Privacy and Verification

## Secrets and authenticated state

Keep credentials in environment variables loaded from ignored `.env`; never commit or print values. NotebookLM authentication lives outside the repository, and `.claude/settings.local.json` remains ignored local configuration. Do not copy either into tasks, specs, fixtures, logs, or commits.

Commands that invoke Nitan MCP, Gemini, NotebookLM, Playwright/browser login, publication, forum posting, scheduled workflows, or live feed checks require explicit task-specific justification. They are prohibited as generic development or migration validation.

## Offline checks

The default repository check is:

```bash
pytest tests/ -v
```

When a pipeline-level smoke test is needed, use the tracked synthetic fixture without briefing or publication:

```bash
EXTRACTION_FIXTURE_PATH=fixtures/sample_extraction.json \
  python run_pipeline.py --skip-briefing --dated
```

Run the smoke test only when its output remains in ignored/disposable locations, and remove disposable output after inspection. Do not add publishing, RSS generation, audio, or network flags.

## Test contracts

- Tests must remain offline and use synthetic/captured fixtures.
- Public compatibility assertions must cover stable feed/site URLs, episode URL shape, and GUID prefix.
- UTF-8 behavior must be asserted with non-ASCII text.
- Optional CastForge, RSS, audio, and browser dependencies must not be imported by unrelated offline paths.
- Never use real unpublished episode content, credentials, forum sessions, or authenticated browser state as fixtures.
