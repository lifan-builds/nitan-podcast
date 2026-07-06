---
id: ctx-context-architecture-decisions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#architecture-decisions
chunk: null
tokens_est: 293
tags: [context, architecture-decisions]
---

# CONTEXT.md: Architecture Decisions

## Summary
CastForge = framework — show repos own schedule, runner, secrets, and published URLs; CastForge provides reusable stages.

## Use when
- working on architecture decisions

## Key facts
- CastForge = framework — show repos own schedule, runner, secrets, and published URLs; CastForge provides reusable stages.
- NotebookLM = audio engine — single place for spoken 简体中文 output.
- Audio hosting: GitHub Pages — serves audio/mpeg; Releases kept as backup (serves application/octet-stream which broke Apple Podcasts).
- Podcast tuning — NOTEBOOKLMAUDIOLENGTH=short + 7 threads + "点到为止" → ~6 min episodes.
- Publication — announcement thread + weekly replies on 美卡论坛; publisher.py generates both.

## Open next
- `CONTEXT.md#architecture-decisions`
