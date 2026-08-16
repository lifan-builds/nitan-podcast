# Bug Analysis: AI Builder shadows stopped before audio generation

## 1. Root Cause Category

- **Category**: E — Implicit Assumption, with a cross-layer request boundary.
- **Specific cause**: Bounding each evidence packet did not bound the total work of one 23–24-candidate GPT-5.6 Terra response. The pipeline also assumed a self-hosted job's start hour was its intended cron slot, which is false after queue delay. macOS sleep was another unmodeled runtime state.

## 2. Why Fixes Failed

1. Compact evidence packets reduced request size but still required one model response to cover every candidate inside 60 seconds.
2. A generic `no-episode-editorial-failure` ledger hid whether the failure was usage gate, timeout, proxy, schema, or coverage.
3. Broad UTC cron coverage plus a current-hour shell gate lost the intended attempt when the runner started late.
4. Keeping the Mac awake manually did not make sleep prevention part of the workflow contract.

## 3. Prevention Mechanisms

| Priority | Mechanism | Specific Action | Status |
| --- | --- | --- | --- |
| P0 | Architecture | Review deterministic batches of at most six and merge only exact per-batch coverage | DONE |
| P0 | Runtime safety | Fail closed before NotebookLM and persist only allowlisted failure type/stage/batch fields | DONE |
| P0 | Scheduling | Map individual UTC cron expressions to intended Pacific slots and dates | DONE |
| P0 | Runner lifecycle | Wrap the episode command with `caffeinate` | DONE |
| P1 | Tests | Cover 23/24 candidates, timeout, invalid values, partial coverage, PDT/PST slots, and workflow wiring | DONE |
| P1 | Live proof | Run one private August 16 shadow and compare public state before/after | DONE |

## 4. Systematic Expansion

- **Similar issues**: Other LLM stages can have bounded inputs but unbounded aggregate response work; any self-hosted scheduled workflow can confuse queue start time with event intent.
- **Design improvement**: Treat external model calls as bounded primitives and keep global coverage validation at the merge boundary.
- **Process improvement**: A successful workflow conclusion is insufficient evidence when generation steps may skip; inspect step outcomes and retained artifacts.

## 5. Knowledge Capture

- [x] Added the executable batching, diagnostic, scheduling, and sleep-prevention contracts to `.trellis/spec/nitan-pod/pipeline-and-editorial.md`.
- [x] Added deterministic regression tests and an independent full-scope review.
- [x] Validated run `31966345117`: 38/38 unique decisions, three qualified primary-sourced stories, 4:29 MP3, transcript, chapters, temporary-source cleanup, and unchanged RSS/R2/releases.
- [x] No shared guide or template tree exists in this project; the domain code-spec is the canonical capture point.
