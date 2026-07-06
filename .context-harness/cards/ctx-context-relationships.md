---
id: ctx-context-relationships
kind: invariant
importance: 0.82
confidence: confirmed
source: CONTEXT.md#relationships
chunk: null
tokens_est: 184
tags: [context, relationships, invariant]
---

# CONTEXT.md: Relationships

## Summary
AGENTS.md is the small activation layer; CONTEXT.md is the durable source of truth, indexed by scripts/context-index.js.

## Use when
- changing architecture or domain relationships
- update context invariants

## Key facts
- AGENTS.md is the small activation layer; CONTEXT.md is the durable source of truth, indexed by scripts/context-index.js.
- An Episode contains one or more Story Briefs.
- A Story Brief is based on exactly one forum thread.
- A Story Brief treats commentary as secondary to factual setup.
- A Story Brief must establish Evidence From Source before interpreting community reaction.

## Open next
- `CONTEXT.md#relationships`
