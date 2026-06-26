# Context Migration Plan

## Goal
Keep active task state separate from durable project context.

## Progress
- [x] Archived oversized NOW.md during context-harness v3 migration.

## Verification
- Run `node scripts/context-index.js check`.

## Archive

### 2026-06-26 Oversized NOW.md Snapshot
```markdown
# Now

## Current Focus

Fixed and verified recent GitHub Actions weekly podcast failures.

## Active Blockers

- None for the weekly workflow; W26 published successfully.
- Context-harness refresh files remain local and uncommitted.

## Immediate Next Step

Decide separately whether to commit the context-harness refresh files.

## Session State

- Last modified: 2026-06-22
- Files touched: `.github/workflows/weekly-export.yml`, `docs/feed.xml`, `docs/episodes/weekly_meika_2026-W26.mp3`, `AGENTS.md`, `CONTEXT.md`, `NOW.md`, `scripts/context-index.js`, context-harness runtime scripts
- Finding: completed recent jobs generated NotebookLM audio successfully but failed in `Create GitHub Release` with `HTTP 401: Requires authentication`.
- Fix: committed and pushed `b2c7fb6` adding `GH_TOKEN: ${{ github.token }}` to the workflow job env.
- Verification: manual workflow run `27985479991` completed successfully and created release `v2026-W26`; workflow commit `217c39a` published the feed and MP3.
```
