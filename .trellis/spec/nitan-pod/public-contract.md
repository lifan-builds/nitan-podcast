# Public Subscriber Contract

## Stable surface

Changes must preserve the values asserted by `public_contract.py` and `tests/test_public_contract.py` unless a task explicitly plans a subscriber migration:

- the public RSS feed and site URLs;
- the episode URL pattern `episodes/weekly_meika_YYYY-Www.mp3`;
- the episode GUID pattern `nitan-podcast-YYYY-Www`;
- `docs/feed.xml` and `docs/episodes/` as publication targets.

Changing these values can make Apple Podcasts or Spotify treat the show as broken or new. Never infer a safe compatibility change from refactoring alone.

## Ownership

This repository owns podcast identity, public URLs, Nitan-specific extraction, category/editorial rules, show assets, RSS output, and tests for these contracts. CastForge owns reusable orchestration and integration stages. Keep `run_pipeline.py` as a thin show-specific composition layer.

## Required validation

Any change that can affect feed identity, episode paths, GUIDs, or RSS output must run the offline public-contract and RSS tests. Live feed validation performs HTTP requests and is not a default development check; run it only when a task explicitly requires external publication verification.
