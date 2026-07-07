---
id: ctx-context-structure
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#structure
chunk: null
tokens_est: 142
tags: [context, structure]
---

# CONTEXT.md: Structure

## Summary
runpipeline.py is the thin CLI that wires show hooks into castforge.pipeline.

## Use when
- working on structure

## Key facts
- runpipeline.py is the thin CLI that wires show hooks into castforge.pipeline.
- extractor.py fetches forum data through nitan-MCP and selects/enriches threads.
- publisher.py creates episode metadata and forum post/reply Markdown.
- rssfeed.py writes the public podcast RSS feed under docs/feed.xml.
- .github/workflows/weekly-export.yml runs the scheduled self-hosted macOS automation.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#structure`
