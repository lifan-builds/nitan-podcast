# Implementation

1. Extend Castforge models/configuration, no-episode behavior, source rendering, duration probing, and length retry; add compatibility and failure tests.
2. Add AI Builder Brief source snapshots, GitHub/Hugging Face momentum, optional X collection, deterministic preprocessing, editorial client/schema, scoring, and ledger generation.
3. Integrate seven-day selection and no-episode flow into atomic publication; update site/config/workflow/docs.
4. Add historical rejection, collector failure, editorial validation, selection, duration, and atomic-publication tests.
5. Run full tests and validation in both repositories, inspect diffs, release Castforge 0.1.2, update the show pin, and publish only after all gates pass.

## Validation

- `python -m pytest` in Castforge.
- `python -m pytest` in AI Builder Brief.
- Fixture run and validation for AI Builder Brief.
- Verify existing feed GUIDs and public URLs are unchanged.
- Verify package build/install and version 0.1.2 before release.
