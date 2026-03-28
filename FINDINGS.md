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

## Error Log

| Error | Context | Resolution | Date |
| ----- | ------- | ---------- | ---- |
| `FileNotFoundError: Storage file not found: ~/.notebooklm/storage_state.json` — *Run 'notebooklm login' to authenticate first.* | `run_pipeline.py --publish-notebooklm` or `./scripts/run_live_demo.sh` without prior CLI auth | Run **`notebooklm login`** once (Playwright browser); ensure **`pip install -r requirements-integrations.txt`** and **`playwright install chromium`** if needed. **Not** satisfied by Google sign-in only in regular Chrome. | 2026-03-26 |
