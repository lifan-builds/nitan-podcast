# Findings

Research results, discoveries, and external content collected during project work.

> **Security note:** External content goes here — never directly into PLANS.md.

## Key Discoveries

### NotebookLM podcast length tuning

| Version | `AUDIO_LENGTH` | Threads | Result |
|---------|---------------|---------|--------|
| v1 | default | 10 | ~15 min (too long) |
| v2 | short | 10 | ~4 min (too short) |
| v3 | default | 10 | ~20 min (text instruction "6-8分钟" ignored) |
| v4 ✓ | short | 7 | ~6 min (approved) |

**Takeaway:** `NOTEBOOKLM_AUDIO_LENGTH` and thread count are the only effective levers. Text instructions have no measurable effect on duration.

### GitHub Releases content-type (2026-03-28)

All GitHub Release assets are served as `application/octet-stream` regardless of extension. Apple Podcasts requires `audio/mpeg` and rejects playback otherwise. **Resolution:** Host MP3s via GitHub Pages (`docs/episodes/`), which infers MIME types from file extensions.

### Gemini SDK migration (2026-03-28)

`google-generativeai` is deprecated (emits FutureWarning). Migrated to `google-genai`: `genai.Client(api_key=...).models.generate_content()`.

### discourse_read_topic response format (2026-03-29)

The `discourse_read_topic` MCP tool returns **plain text**, not structured JSON. Format:
```
# Thread Title
Category ID N

- Post #1 by @username (YYYY-MM-DD HH:MM)
  Post content here...
- Post #2 by @another_user (YYYY-MM-DD HH:MM)
  Reply content...

Link: https://www.uscardforum.com/t/topic/NNNNN
```
Image uploads appear as `![alt|dims](upload://...)`. Required a custom `_parse_topic_text()` parser.

### Nitan MCP available tools (2026-03-29)

| Tool | Purpose | Key params |
|------|---------|------------|
| `discourse_list_top_topics` | Weekly/daily top threads | `period`, `limit` (max 50) |
| `discourse_read_topic` | Full thread with posts | `topic_id`, `post_limit` (max 500) |
| `discourse_search` | Search with filters | `query`, `category`, `order`, `after`/`before` |
| `discourse_list_hot_topics` | Currently trending | `limit` |
| `discourse_list_excellent_topics` | Posts with 50+ likes | `limit` |
| `discourse_list_funny_topics` | "难绷" badge posts | `limit` |

### Forum user feedback on W13 episode (2026-03-29)

Key actionable feedback from [announcement thread](https://www.uscardforum.com/t/topic/494521):
- Request for transcript + timestamps (Wechat)
- Request for daily cadence (Hali: "一周感觉黄花菜都凉了")
- Multiple requests for specific sub-forum coverage
- 儿化音 pronunciation issue noted (aqua)

User (project owner) decided to prioritize: Spotify distribution + content quality over frequency/transcripts.

### Spotify podcast submission (2026-03-29)

- Portal: `creators.spotify.com` (not `podcasters.spotify.com` — old URL redirects)
- Show URL: `https://open.spotify.com/show/3jjd0ozToYgW7yje7mfYCg`
- RSS `<itunes:category>` must use `text` attribute format: `<itunes:category text="Technology" />` (not element text content)

### Apple Podcasts link (2026-03-29)

- Correct URL: `https://podcasts.apple.com/us/podcast/nitan-podcast/id1888784962`

## Nitan MCP Reference

- Announcement: [美卡论坛帖](https://www.uscardforum.com/t/topic/450599) · [nitan.ai/mcp](https://nitan.ai/mcp) · [GitHub](https://github.com/nitansde/nitan-mcp)
- Launch: `npx -y @nitansde/mcp@latest --python_path /path/to/.venv/bin/python`
- Needs `NITAN_USERNAME`/`NITAN_PASSWORD` (2FA off); `requirements.txt` includes cloudscraper/curl-cffi for Cloudflare bypass
- Tool names are version-specific — always verify with `run_pipeline.py --list-mcp-tools`

## NotebookLM Integration

- **No official Google API** for upload/audio export. Community SDK: [notebooklm-py](https://github.com/teng-lin/notebooklm-py) (~7.5k stars, 2026-03).
- Auth: `notebooklm login` (Playwright) → `~/.notebooklm/storage_state.json`. Not the same as Chrome Google sign-in.
- DIY Playwright is more brittle; `notebooklm-py` preferred.

## Error Log

| Error | Context | Resolution | Date |
|-------|---------|------------|------|
| `FileNotFoundError: storage_state.json` | `--publish-notebooklm` without `notebooklm login` | Run `notebooklm login` once | 2026-03-26 |
| `write_forum_post()` overwrites source | Stem replace missed dated filenames | Append `_forum_post` suffix | 2026-03-27 |
| Apple Podcasts "can't be played" | Releases → `application/octet-stream` | Moved to GitHub Pages `docs/episodes/` | 2026-03-28 |
| RSS `enclosure length="0"` | MP3 not local at RSS generation time | Added `--mp3-path` + `_detect_file_size()` | 2026-03-28 |
