# Findings

Research results, discoveries, and external content collected during project work.

> **Security note:** External content (web searches, API responses, copied docs) goes here — never directly into `PLANS.md`. This separation prevents untrusted content from polluting the trusted execution plan.

## Research & References

### NotebookLM as the product audio engine (project stance)

The stack is **NotebookLM-first**: Python prepares **sources**; **Audio Overview** (or similar) in **Google NotebookLM** is the **key solution** for the weekly **Chinese podcast**. There is **no reliance** on a public NotebookLM API for the supported workflow.

### Official API

**Google NotebookLM** does not expose a documented **public API** for programmatic source upload or **Audio Overview** export (as of research captured here). The **supported** integration is: generate **UTF-8 Markdown** on disk → user **uploads** in the NotebookLM UI → generates audio there. Revisit if Google publishes an official API.

### Third-party GitHub integrations (research, 2026-03)

There is still **no official Google NotebookLM API**. Community projects fall into **(A) reverse-engineered / internal RPC clients**, **(B) MCP servers wrapping NotebookLM**, **(C) Playwright-style browser automation**, and **(D) alternatives that replace NotebookLM’s podcast feature**.

| Project | Stars (approx.) | Role | Notes |
| ------- | ----------------- | ---- | ----- |
| [**teng-lin/notebooklm-py**](https://github.com/teng-lin/notebooklm-py) | ~7.5k | **Unofficial Python SDK + CLI** ([PyPI `notebooklm-py`](https://pypi.org/project/notebooklm-py/)) | Uses **undocumented Google APIs**; notebooks, **sources** (URL/file/Markdown), **Audio Overview** generation (**formats / lengths / languages**), **wait + download MP3/MP4**, plus video/slides/quiz/etc. Optional **`pip install "notebooklm-py[browser]"`** + **`playwright install chromium`** for **`notebooklm login`**. **Strongest fit** to chain after `export_for_notebooklm`: add file → `generate_audio` with **中文** instructions → download. **Risks:** APIs can break anytime; not Google-affiliated; credentials stored locally — see repo [Security](https://github.com/teng-lin/notebooklm-py/blob/main/SECURITY.md) and [Troubleshooting](https://github.com/teng-lin/notebooklm-py/blob/main/docs/troubleshooting.md). |
| [**PleasePrompto/notebooklm-skill**](https://github.com/PleasePrompto/notebooklm-skill) | ~5k | **Claude Code skill** | Browser automation, persistent auth, Q&A over notebooks — agent-centric vs a small automated weekly job. |
| [**khengyun/notebooklm-mcp**](https://github.com/khengyun/notebooklm-mcp) | ~80 | **MCP server** for NotebookLM | Exposes NotebookLM to MCP clients; compare if you want **NotebookLM-as-tool** vs direct Python. |
| [**DataNath/notebooklm_source_automation**](https://github.com/DataNath/notebooklm_source_automation) | ~50 | **Playwright** source upload | Focused on adding **web** sources in bulk, not the full generate-audio pipeline. |
| [**Pantheon-Security/notebooklm-mcp-secure**](https://github.com/Pantheon-Security/notebooklm-mcp-secure) | ~40 | Hardened **MCP** | Security-hardened MCP wrapper pattern. |
| [**proyecto26/notebooklm-ai-plugin**](https://github.com/proyecto26/notebooklm-ai-plugin) | smaller | Agent plugin | Mentions slides/audio; verify vs `notebooklm-py` maturity. |
| [**omril321/automated-notebooklm**](https://github.com/omril321/automated-notebooklm) | smaller | Automation + integrations | e.g. external boards — different shape than weekly export. |
| [**souzatharsis/podcastfy**](https://github.com/souzatharsis/podcastfy) | ~6k | **OSS “podcast from content”** | Alternative to NotebookLM **audio** — not an integration with Google. |

**Recommendation for nitan-pod:** Prefer **[notebooklm-py](https://github.com/teng-lin/notebooklm-py)** for **programmatic** upload + **Audio Overview** + **download** in one Python-friendly package. Wire as an **optional** post-step to `run_pipeline.py` via **`--publish-notebooklm`** (and **`scripts/run_live_demo.sh`**) after **`notebooklm login`** (**interactive**; **CI** usually needs a different credential story or **local-only** runs).

**Implementation (nitan-pod):** [`notebooklm_audio.py`](notebooklm_audio.py) + `run_pipeline.py --publish-notebooklm`; optional deps in [`requirements-integrations.txt`](requirements-integrations.txt). Language default **`zh`**; generation uses **only** the newly uploaded source id.

### Unofficial Path — DIY Playwright on the NotebookLM web UI

Possible but **more brittle** than **`notebooklm-py`** unless you need something the SDK lacks. **Cons:** DOM churn, session/login, ToS ambiguity.

This remains **optional** per [`PLANS.md`](PLANS.md) unless we explicitly adopt an SDK or MCP wrapper.

### Nitan MCP (USCardForum / 泥潭)

Official announcement and setup guide (美卡论坛): [**【Nitan MCP】你的专属泥潭AI助手**](https://www.uscardforum.com/t/topic/450599). Project site: [nitan.ai/mcp](https://nitan.ai/mcp). Source: [**github.com/nitansde/nitan-mcp**](https://github.com/nitansde/nitan-mcp) (`MCP client and Skill for US Card Forum`).

**Typical stdio launch (matches Claude Desktop / thread examples):**

- Command: `npx`
- Args: `["-y", "@nitansde/mcp@latest"]` (pin a version in production if you prefer, e.g. `@nitansde/mcp@x.y.z`)
- **Important for this repo:** append **`--python_path`** pointing at **`nitan-pod/.venv/bin/python`** after `pip install -r requirements.txt`. Nitan MCP shells out to Python for **cloudscraper** / **curl_cffi**; without a venv that has those packages, startup can hit **403 / Cloudflare** or “Python script produced no output” (see forum [FAQ](https://www.uscardforum.com/t/topic/450599)).

**Server environment (passed through to the MCP process — also set in your `.env` for `run_pipeline.py`):**

- `NITAN_USERNAME` / `NITAN_PASSWORD` — forum login; thread notes many features need login and **2FA should be disabled** on the forum account for this flow.
- `TIME_ZONE` or `TIMEZONE` — e.g. `America/Los_Angeles`, `Asia/Shanghai` (thread mentions both naming; follow current package README if unsure).

**Tools (names evolve with releases — always run `python run_pipeline.py --list-mcp-tools`):** release notes in the thread mention Discourse-oriented tools such as **`discourse_search`** (filters: category, author, `after`/`before`, sort), **`discourse_list_top_topics`**, **`discourse_list_hot_topics`**, **`discourse_read_topic`**, notifications / user activity tools, etc. For a **weekly digest**, a good starting point is often **`discourse_list_hot_topics`** or **`discourse_list_top_topics`** with the appropriate **period** parameter as defined by the live tool schema — then optionally **`discourse_read_topic`** per `topic_id` for bodies/replies. Exact JSON for `MCP_EXTRACT_TOOL_ARGUMENTS` depends on the tool schema your server exposes.

**Operational caveats (from thread):** Cloudflare / CSRF issues can affect login or automation; `curl_cffi` / browser paths may be required on some hosts; rate limits and 403 if unauthenticated or too aggressive.

## Discoveries

- **`google.generativeai` deprecation:** As of 2026, importing `google.generativeai` may log a **FutureWarning** directing users to the newer **`google.genai`** SDK. `briefing_writer.py` still uses `google-generativeai` from `requirements.txt`; consider migrating to `google.genai` in a follow-up when stable for your environment.

- **NotebookLM GitHub landscape (2026-03):** GitHub API `search/repositories?q=notebooklm` surfaces **`teng-lin/notebooklm-py`** as the highest-star project with explicit **Audio Overview** + **download** docs; **`PleasePrompto/notebooklm-skill`** and several **`notebooklm-mcp`** repos target agents/MCP rather than a minimal weekly pipeline. Star counts drift over time — re-check before adopting.

### SoundCloud API registration closed (~2018)

**Status:** SoundCloud stopped accepting new API app registrations around 2018. Attempting to register at [soundcloud.com/you/apps](https://soundcloud.com/you/apps) returns "Something went wrong while creating the app." This is a known, long-standing issue confirmed by multiple developer reports and SoundCloud's own developer portal.

**Impact on nitan-podcast:** `soundcloud_upload.py` was created with full OAuth 2.1 PKCE flow but is **unusable** without an existing registered app's `SOUNDCLOUD_CLIENT_ID` / `SOUNDCLOUD_CLIENT_SECRET`. The code is kept in case access opens or someone with an existing app ID contributes.

**Workaround for forum audio:** If a user manually uploads an MP3 via [soundcloud.com](https://soundcloud.com) (free tier, no API needed), the resulting track URL auto-embeds on Discourse via onebox. This is the most promising near-term path for inline playback on 美卡论坛.

### 美卡论坛 MP3 upload restriction

The forum only allows image uploads: `jpg, jpeg, png, gif, heic, heif, webp, avif, svg`. No admin override is available to regular users. Discourse's built-in `![name|audio](upload://...)` audio player syntax works **only** with server-hosted audio files, which requires admin to whitelist `.mp3` in site settings (`authorized_extensions`).

**Options explored:**
1. ~~Direct MP3 upload~~ — blocked by extension whitelist
2. ~~SoundCloud API~~ — app registration closed
3. **SoundCloud manual upload** — free tier track URL auto-embeds via Discourse onebox ✓ (manual)
4. **GitHub Releases download link** — works but no inline player (current interim)
5. **Ask forum admin** to add `mp3` to `authorized_extensions` — untested
6. **Spotify for Podcasters** — would need admin to whitelist iframe/embed domain

### NotebookLM podcast length tuning (4 iterations)

| Version | `AUDIO_LENGTH` | Threads | Instructions | Result |
|---------|---------------|---------|--------------|--------|
| v1 | default | 10 | basic 中文 | ~15 min (too long) |
| v2 | short | 10 | basic 中文 | ~4 min (too short) |
| v3 | default | 10 | + "6-8分钟" constraint | ~20 min (instruction ignored) |
| v4 ✓ | short | 7 | fast pace, keyword hooks, "点到为止" | ~6 min (approved) |

**Key finding:** `NOTEBOOKLM_AUDIO_LENGTH` and thread count are the effective levers. Text instructions requesting a specific duration have no measurable effect.

## Error Log

| Error | Context | Resolution | Date |
| ----- | ------- | ---------- | ---- |
| `FileNotFoundError: Storage file not found: ~/.notebooklm/storage_state.json` — *Run 'notebooklm login' to authenticate first.* | `run_pipeline.py --publish-notebooklm` or `./scripts/run_live_demo.sh` without prior CLI auth | Run **`notebooklm login`** once (Playwright browser); ensure **`pip install -r requirements-integrations.txt`** and **`playwright install chromium`** if needed. **Not** satisfied by Google sign-in only in regular Chrome. | 2026-03-26 |
| SoundCloud app registration: "Something went wrong while creating the app" | User attempted to register at soundcloud.com/you/apps | **No fix** — SoundCloud API registration closed since ~2018. See research above. | 2026-03-27 |
| 美卡论坛 MP3 upload: "不被允许（允许的扩展名：jpg, jpeg, png, gif...）" | Attempted drag-and-drop MP3 upload in Discourse editor | **No fix** for regular users — admin must add `mp3` to `authorized_extensions`. Workaround: GitHub Release download link. | 2026-03-27 |
| `write_forum_post()` overwrites NotebookLM source | `stem.replace("notebooklm", "forum_post")` didn't match dated filenames like `weekly_meika_2026-W13.md` | Fixed: check if "notebooklm" is in stem; if not, append `_forum_post` suffix. | 2026-03-27 |
