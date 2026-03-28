"""
Episode metadata and forum post generator for weekly podcast publication.

Produces:
- Chinese episode metadata (title, description)
- Announcement post (initial thread for 美卡论坛, Nitan MCP style)
- Weekly episode reply (posted as a reply in the announcement thread)
"""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

SERIES_NAME = "Nitan Podcast"
SERIES_ZH = "泥潭播客"
TAGLINE = "你的每周美卡论坛精华AI播客"

# RSS / Podcast distribution defaults (overridable via env vars)
PODCAST_LINK = "https://lifan-builds.github.io/nitan-podcast/"
PODCAST_DESCRIPTION = "每周精选美卡论坛（泥潭）热帖，AI 自动生成的中文播客。6-8 分钟听完一周精华。"
PODCAST_LANGUAGE = "zh"
PODCAST_CATEGORY = "Technology"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_week_label() -> str:
    """Return e.g. '2026年第13周'."""
    iso = date.today().isocalendar()
    return f"{iso.year}年第{iso.week}周"


def episode_guid(week_label: str | None = None) -> str:
    """Stable GUID for an episode, e.g. 'nitan-podcast-2026-W13'."""
    label = week_label or current_week_label()
    m = re.match(r"(\d{4})年第(\d+)周", label)
    if m:
        return f"nitan-podcast-{m.group(1)}-W{int(m.group(2)):02d}"
    return f"nitan-podcast-{label}"


def _extract_threads(markdown: str) -> list[dict[str, str]]:
    """Pull thread metadata from exported Markdown."""
    threads: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in markdown.splitlines():
        m = re.match(r"^-\s+\*\*(\w+)\*\*[：:]\s*(.+)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current[key] = val
        elif line.startswith("## 线索") and current:
            threads.append(current)
            current = {}
    if current:
        threads.append(current)
    return threads


def _extract_thread_titles(markdown: str) -> list[str]:
    """Pull thread titles from exported Markdown."""
    return [t["title"] for t in _extract_threads(markdown) if "title" in t]


# ---------------------------------------------------------------------------
# Episode metadata
# ---------------------------------------------------------------------------

def episode_metadata(
    markdown: str,
    *,
    week_label: str | None = None,
) -> dict[str, str]:
    """Return episode title and description (Chinese) derived from the export Markdown."""
    label = week_label or current_week_label()
    title = f"【{SERIES_NAME}】{SERIES_ZH} · {label}"

    threads = _extract_threads(markdown)
    titles = [t.get("title", "") for t in threads if t.get("title")]
    if titles:
        bullets = "\n".join(f"- {t}" for t in titles)
        description = f"本期话题：\n{bullets}"
    else:
        description = f"{SERIES_ZH} {label} 精选话题"

    return {
        "title": title,
        "description": description,
        "week_label": label,
        "threads": threads,
    }


# ---------------------------------------------------------------------------
# Announcement post (initial thread — post once, edit to update)
# ---------------------------------------------------------------------------

def announcement_post_markdown() -> str:
    """Generate the initial 美卡论坛 announcement thread, Nitan MCP style."""
    return f"""\
# 【{SERIES_NAME}】{TAGLINE}

## 这是什么？

**{SERIES_NAME}**（{SERIES_ZH}）是一档由 AI 自动生成的**每周播客**，帮你用 **6-8 分钟**听完本周美卡论坛（泥潭）最火的帖子。

每周自动：
1. 通过 **Nitan MCP** 抓取本周热帖
2. 用 **Google NotebookLM** 生成双人中文播客
3. 发布音频 + 话题列表到论坛

**不用翻帖子，通勤路上听完一周精华。**

## 收听方式

每周更新会以**回复**的形式发在本帖下方，包含：
- 本期音频链接
- 本周话题列表（带原帖链接）
- 热度数据（浏览量、点赞数）

> 后续也会上线播客平台（小宇宙 / Spotify 等），敬请期待。

## 技术栈

- [**Nitan MCP**](https://www.uscardforum.com/t/topic/450599) — 论坛数据抓取
- **Google NotebookLM** — AI 播客生成
- **Python** 自动化 pipeline（[开源](https://github.com/lifan-builds/nitan-podcast)，欢迎 star :star:）

## FAQ

**Q: 播客内容准确吗？**
A: 内容严格基于论坛原帖，AI 不会编造信息。但 AI 生成的口播可能有细节偏差，建议感兴趣的话题点开原帖看看。

**Q: 为什么有些热帖没提到？**
A: 每期选取本周 Top 7 热帖，覆盖不了所有内容。有想听的话题可以留言告诉我。

**Q: 更新频率？**
A: 每周一期，通常周末或周一发布。

**Q: 可以自己跑这个 pipeline 吗？**
A: 可以！代码开源，README 有完整教程。需要 Nitan MCP + NotebookLM 账号。

---

*有建议或想听的内容？直接回帖告诉我！*
"""


# ---------------------------------------------------------------------------
# Weekly episode reply (posted as reply in the announcement thread)
# ---------------------------------------------------------------------------

def episode_reply_markdown(
    metadata: dict[str, str],
    *,
    audio_url: str | None = None,
    extra_links: dict[str, str] | None = None,
) -> str:
    """Generate a weekly episode reply for the announcement thread."""
    lines: list[str] = []

    # Header
    lines.append(f"# {SERIES_ZH} · {metadata['week_label']}")
    lines.append("")

    # Audio link — if audio_url looks like an upload reference, use Discourse
    # audio embed syntax; otherwise show a download link.
    if audio_url:
        if audio_url.startswith("upload://"):
            lines.append(f"![{SERIES_ZH}-{metadata['week_label']}|audio]({audio_url})")
        else:
            lines.append(f":headphones: **收听本期：** {audio_url}")
        lines.append("")

    # Topic table with links and stats
    threads = metadata.get("threads", [])
    if threads:
        lines.append("## 本期话题")
        lines.append("")
        lines.append("| # | 话题 | 分类 | :heart: | :eyes: |")
        lines.append("|---|------|------|---------|--------|")
        for i, t in enumerate(threads, 1):
            title = t.get("title", "—")
            url = t.get("url", "")
            cat = t.get("category", "")
            likes = t.get("like_count", "")
            views = t.get("views", "")
            title_cell = f"[{title}]({url})" if url else title
            lines.append(f"| {i} | {title_cell} | {cat} | {likes} | {views} |")
        lines.append("")

    # Extra platform links
    if extra_links:
        lines.append("**其他平台：**")
        link_parts = [f"[{name}]({url})" for name, url in extra_links.items()]
        lines.append(" · ".join(link_parts))
        lines.append("")

    if not audio_url:
        lines.append("> :point_up: 发帖时将 MP3 文件拖入编辑器即可生成内嵌播放器")
        lines.append("")

    lines.append("---")
    lines.append(f"*由 {SERIES_NAME} 自动生成 · {metadata['week_label']}*")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------

def write_announcement_post(output_path: Path | None = None) -> Path:
    """Write the announcement thread to disk."""
    post = announcement_post_markdown()
    out = Path(output_path or "exports/nitan_podcast_announcement.md").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(post, encoding="utf-8")
    logger.info("Wrote announcement post: %s", out)
    return out


def write_forum_post(
    markdown_export_path: Path,
    output_path: Path | None = None,
    *,
    audio_url: str | None = None,
    extra_links: dict[str, str] | None = None,
) -> Path:
    """Read the exported Markdown, generate an episode reply, write to disk."""
    md_path = Path(markdown_export_path).resolve()
    md_content = md_path.read_text(encoding="utf-8")

    meta = episode_metadata(md_content)
    post = episode_reply_markdown(meta, audio_url=audio_url, extra_links=extra_links)

    if output_path is None:
        stem = md_path.stem
        if "notebooklm" in stem:
            new_stem = stem.replace("notebooklm", "forum_post")
        else:
            new_stem = stem + "_forum_post"
        output_path = md_path.parent / f"{new_stem}{md_path.suffix}"

    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(post, encoding="utf-8")
    logger.info("Wrote forum post: %s", out)
    return out
