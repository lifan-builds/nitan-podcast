# Design

Castforge owns generic schema-v2 contracts, minimum-story gating, source-document rendering, MP3 duration probing, and NotebookLM length retry. AI Builder Brief owns source collection, snapshots, X discovery, deterministic exclusions/clustering, CLIProxyAPI editorial judgment, selection policy, ledger output, and show publication behavior.

Candidates are collected for seven days and enriched from retained snapshots. Deterministic rules reject known filler and pre-rank at most 24 qualified clusters. A localhost-only client runs the configured usage gate and requests strict JSON from GPT-5.6 Terra. Local validation checks exact candidate coverage and computes the approved weighted score and deterministic diversity ordering. Any missing dependency or invalid response returns `no-episode` before audio generation.

Selected judgments are copied into `StoryCluster.metadata` and all candidate decisions into an editorial ledger. Castforge generates the source and audio in staging, measures duration with `ffprobe`, retries once at short length above 15 minutes, and exposes no public feed mutation until all show-owned transcription, upload, and validation stages succeed.

Schema version 2 reads version-1 manifests by defaulting new fields. `analysis` sources qualify only expert-analysis clusters backed by a factual primary source or two independent sources; analysis alone cannot qualify technical claims.
