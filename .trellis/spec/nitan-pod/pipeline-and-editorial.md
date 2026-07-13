# Pipeline and Editorial Contracts

## Data flow

Preserve structured `threads: list[dict]` through extraction and publication. Do not regex-reparse rendered text when structured thread data is available. `EXTRACTION_FIXTURE_PATH` is the offline input boundary for deterministic pipeline tests.

Use `encoding="utf-8"` for text file reads and writes. Podcast and source output includes Chinese text, so platform-default encoding is not acceptable.

Keep RSS and CastForge audio imports lazy where the CLI currently defers them. Importing offline commands and test modules must not require optional audio/browser integrations.

## Editorial ordering

An episode contains one or more Story Briefs, each grounded in exactly one forum thread. A Story Brief must establish thread-specific evidence, stakes, caveats, and informative replies before commentary or light banter. Prefer replies that add facts, corrections, constraints, firsthand data, or substantive interpretation; do not elevate usernames, likes, jokes, or reaction-only replies as evidence.

The Source Document owns factual Story Brief structure before any NotebookLM audio style is applied. Category voice guidance is prescriptive and reviewed; it may shape presentation but must not substitute for evidence or mimic forum mood verbatim.

## Integration boundaries

Nitan MCP topic details require the repository parser because `discourse_read_topic` returns formatted text rather than JSON. Test parser changes with captured synthetic fixtures. Do not use live forum calls as routine validation.
