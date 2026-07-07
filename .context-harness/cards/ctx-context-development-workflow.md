---
id: ctx-context-development-workflow
kind: workflow
importance: 0.65
confidence: confirmed
source: CONTEXT.md#development-workflow
chunk: null
tokens_est: 147
tags: [context, development-workflow, workflow]
---

# CONTEXT.md: Development Workflow

## Summary
Copy .env.example → .env; configure MCP + optional GEMINIAPIKEY + NOTEBOOKLM.

## Use when
- working on development workflow

## Key facts
- Copy .env.example → .env; configure MCP + optional GEMINIAPIKEY + NOTEBOOKLM.
- For local dev without a pip-installed CastForge, keep a sibling checkout at ../castforge or install with pip install -e ../castforge.
- python runpipeline.py (add --dated, --publish-notebooklm, --generate-post, --generate-rss as needed).
- Tests: pytest tests/ -v (offline, sub-second). Smoke: EXTRACTIONFIXTUREPATH=fixtures/sampleextraction.json python runpipeline.py --skip-briefing --dated.
- Feed check: python scripts/validatefeed.py (local) or live URL.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#development-workflow`
