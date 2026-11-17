# Nitan Podcast

- This repository owns Nitan/USCardForum MCP extraction, category voice rules (`editorial/category_voice.yaml`), Chinese forum post drafts, GitHub Pages RSS/MP3 assets, and the Sunday self-hosted runner workflow; reusable stages live in `castforge`.
- Subscriber-facing URLs and GUID formats in `public_contract.py`, `docs/feed.xml`, and `docs/episodes/*.mp3` are immutable (`nitan-podcast-YYYY-Www`, `weekly_meika_YYYY-Www.mp3`) — never alter historical episodes or feed URLs.
- Runner secrets (`~/.nitan-podcast/.env`) and NotebookLM Playwright auth state stay outside git; `scripts/prepare_audio.py` enforces a verified MP3 container and measured duration before release or RSS updates.
