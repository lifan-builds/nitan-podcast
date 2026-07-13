# Nitan Pod Engineering Specifications

Nitan Pod is the public show repository for the Nitan Podcast. It owns the show identity, Nitan/USCardForum-specific extraction and editorial behavior, RSS/publication assets, and scheduled workflow integration. Reusable pipeline stages belong to CastForge.

## Source-of-truth order

1. `.trellis/spec/nitan-pod/` for durable engineering and safety contracts.
2. The active `.trellis/tasks/` artifact for task-specific requirements and decisions.
3. `public_contract.py` and `tests/test_public_contract.py` for subscriber-facing compatibility constants.
4. `podcast.yaml`, implementation, and offline tests for executable pipeline behavior.
5. `README.md` and `docs/` for user-facing operation and architecture.

## Specifications

- [Public subscriber contract](public-contract.md)
- [Pipeline and editorial contracts](pipeline-and-editorial.md)
- [Privacy and verification](privacy-and-verification.md)
