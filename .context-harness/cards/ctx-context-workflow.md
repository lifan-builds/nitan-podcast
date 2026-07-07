---
id: ctx-context-workflow
kind: workflow
importance: 0.9
confidence: confirmed
source: CONTEXT.md#workflow
chunk: null
tokens_est: 137
tags: [context, workflow]
---

# CONTEXT.md: Workflow

## Summary
Local setup: copy .env.example to .env, configure MCP, optional Gemini, and NotebookLM variables.

## Use when
- running, testing, linting, deploying, deployment, or verifying changes

## Key facts
- Local setup: copy .env.example to .env, configure MCP, optional Gemini, and NotebookLM variables.
- CastForge is expected from a sibling ../castforge checkout or pip install -e ../castforge.
- Main run: python runpipeline.py, with flags such as --dated, --publish-notebooklm, --generate-post, and --generate-rss.
- Offline tests: pytest tests/ -v.
- Fixture smoke: EXTRACTIONFIXTUREPATH=fixtures/sampleextraction.json python runpipeline.py --skip-briefing --dated.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#workflow`
