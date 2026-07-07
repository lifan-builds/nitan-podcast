---
id: ctx-context-coding-conventions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#coding-conventions
chunk: null
tokens_est: 120
tags: [context, coding-conventions]
---

# CONTEXT.md: Coding Conventions

## Summary
NotebookLM-first — Python serves sources, NotebookLM serves audio.

## Use when
- working on coding conventions

## Key facts
- NotebookLM-first — Python serves sources, NotebookLM serves audio.
- UTF-8 everywhere — encoding="utf-8" on all file I/O.
- Secrets — env vars only; never commit .env.
- Structured data passthrough — pass threads: list[dict] through the pipeline; avoid regex re-parsing when threads are available.
- Lazy imports — rssfeed and CastForge audio path stay lazy where the CLI already did; compatibility modules import CastForge on load (lightweight).

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#coding-conventions`
