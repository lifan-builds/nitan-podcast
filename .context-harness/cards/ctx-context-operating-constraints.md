---
id: ctx-context-operating-constraints
kind: constraints
importance: 0.9
confidence: confirmed
source: CONTEXT.md#operating-constraints
chunk: null
tokens_est: 115
tags: [context, operating-constraints, constraints]
---

# CONTEXT.md: Operating Constraints

## Summary
NotebookLM is the audio engine; Python prepares sources and publication artifacts.

## Use when
- before planning or editing
- checking project constraints
- update context safely

## Key facts
- NotebookLM is the audio engine; Python prepares sources and publication artifacts.
- Preserve the subscriber contract in publiccontract.py and tests/testpubliccontract.py.
- Use UTF-8 for file I/O.
- Keep secrets in environment variables only; never commit .env.
- Preserve structured threads: list[dict] data through the pipeline instead of regex re-parsing when available.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#operating-constraints`
