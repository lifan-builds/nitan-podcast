---
id: ctx-context-project-structure
kind: project
importance: 0.65
confidence: confirmed
source: CONTEXT.md#project-structure
chunk: null
tokens_est: 361
tags: [context, project-structure, project]
---

# CONTEXT.md: Project Structure

## Summary
| Path | Role |

## Use when
- working on project structure

## Key facts
- | Path | Role |
- | ---- | ---- |
- | runpipeline.py | Thin CLI: wires show hooks into castforge.pipeline |
- | castforge.py | Resolves CastForge import (sibling checkout or venv install) |
- | publiccontract.py | Stable public feed/episode URLs and GUID prefix — do not break subscribers |

## Open next
- `CONTEXT.md#project-structure`
