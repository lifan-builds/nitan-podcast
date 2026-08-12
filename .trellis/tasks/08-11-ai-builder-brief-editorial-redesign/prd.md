# AI Builder Brief editorial redesign

## Goal

Replace fixed-score top-five selection with an auditable, decision-changing editorial pipeline that monitors seven days of evidence and publishes only when at least three developments materially affect AI builders.

## Requirements

- Collect first-party frontier changes, GitHub/Hugging Face momentum, actionable research, and optional expert observations from the approved X panel.
- Reject routine releases, roundups, cloud wrappers, marketing, release candidates, CI-only changes, weak model cards, and research without practical impact.
- Use deterministic preprocessing, then strict-schema GPT-5.6 Terra review through localhost CLIProxyAPI; any editorial infrastructure failure produces no episode.
- Select 3–6 qualified stories using the approved thresholds, weights, and diversity penalties; allow at most one deep item.
- Publish an auditable editorial ledger and richer NotebookLM source document.
- Generate default-length audio, retry over-15-minute output once with short, measure actual MP3 duration, and leave RSS unchanged on any failure.
- Preserve existing public URLs, GUIDs, daily attempt schedule, and 9 GB R2 hard cap.
- Release Castforge 0.1.2 with schema-v2 contracts and pin AI Builder Brief to it.

## Acceptance criteria

- Historical low-value examples are rejected by tests.
- Zero to two qualifying stories exit successfully as `no-episode` without audio or RSS mutation.
- Three to six qualifying stories are deterministic, evidence-qualified, and fully auditable.
- X outages do not block collection; proxy/schema/usage-gate failures fail closed.
- Actual audio duration is written to manifest and RSS; audio over 15 minutes is never published.
- Both repositories pass their focused and full test suites, and public feed/GUID compatibility remains intact.
