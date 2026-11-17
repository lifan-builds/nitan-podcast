"""
Episode metadata and forum reply generator for weekly podcast publication.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from pathlib import Path

from public_contract import PUBLIC_SITE_URL, SERIES_GUID_PREFIX

logger = logging.getLogger(__name__)

SERIES_NAME = "Nitan Podcast"
SERIES_ZH = "泥潭播客"

# RSS / Podcast distribution defaults (overridable via env vars)
PODCAST_LINK = PUBLIC_SITE_URL
PODCAST_DESCRIPTION = "每周精选美卡论坛（泥潭）热帖，AI 自动生成的中文播客。6-8 分钟听完一周精华。"
PODCAST_LANGUAGE = "zh"
PODCAST_CATEGORY = "Technology"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def current_week_label() -> str:
    """Return e.g. '2026年第13周' or a custom label if EPISODE_LABEL is set."""
    if custom := os.environ.get("EPISODE_LABEL"):
        return custom
    iso = date.today().isocalendar()
    return f"{iso.year}年第{iso.week}周"


def episode_guid(week_label: str | None = None) -> str:
    """Stable GUID for an episode, e.g. 'nitan-podcast-2026-W13'."""
    label = week_label or current_week_label()
    m = re.match(r"(\d{4})年第(\d+)周", label)
    if m:
        return f"{SERIES_GUID_PREFIX}-{m.group(1)}-W{int(m.group(2)):02d}"
    return f"{SERIES_GUID_PREFIX}-{label}"


def _extract_threads(markdown: str) -> list[dict[str, str]]:
    """Pull thread metadata from exported Markdown."""
    threads: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in markdown.splitlines():
        m = re.match(r"^-\s+\*\*(\w+)\*\*[：:]\s*(.+)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            current[key] = val
        elif (line.startswith("## 线索") or line.startswith("## Story Brief")) and current:
            threads.append(current)
            current = {}
    if current:
        threads.append(current)
    return threads


# ---------------------------------------------------------------------------
# Episode metadata
# ---------------------------------------------------------------------------

def _format_description(threads: list[dict[str, str]], label: str) -> str:
    """Build a rich show-note description from thread metadata."""
    if not threads:
        return f"{SERIES_ZH} {label} 精选话题"

    lines: list[str] = []

    # Highlights teaser — pick top 2-3 threads by engagement for hooks
    top_hooks = sorted(threads, key=lambda t: int(t.get("like_count", 0)), reverse=True)[:3]
    hook_titles = [t.get("title", "")[:20] for t in top_hooks if t.get("title")]
    if hook_titles:
        lines.append(f"本期看点：{'、'.join(hook_titles)}……")
        lines.append("")

    # Group threads by category
    by_cat: dict[str, list[dict[str, str]]] = {}
    for t in threads:
        cat = t.get("category", "其他")
        by_cat.setdefault(cat, []).append(t)

    # Summary line
    cats = " / ".join(by_cat.keys())
    total_views = sum(int(t.get("views", 0)) for t in threads)
    lines.append(f"本期精选 {len(threads)} 个热帖，涵盖{cats}。")
    if total_views > 0:
        lines.append(f"本周合计 {total_views:,} 次浏览。")
    lines.append("")

    # Threads grouped by category with stats
    for cat, cat_threads in by_cat.items():
        lines.append(f"【{cat}】")
        for t in cat_threads:
            title = t.get("title", "—")
            likes = t.get("like_count", "")
            views = t.get("views", "")
            posts_count = t.get("posts_count", t.get("reply_count", ""))
            stat_parts = []
            if likes:
                stat_parts.append(f"❤️{likes}")
            if views:
                stat_parts.append(f"👀{views}")
            if posts_count:
                stat_parts.append(f"💬{posts_count}")
            stat = " ".join(stat_parts)
            lines.append(f"• {title}" + (f"  ({stat})" if stat else ""))
            # Add teaser from OP content if available
            op = t.get("op_content", t.get("op_summary", ""))
            if op:
                teaser = op[:60].rstrip() + ("…" if len(op) > 60 else "")
                lines.append(f"  └ {teaser}")
        lines.append("")

    return "\n".join(lines).strip()


def episode_metadata(
    markdown: str,
    *,
    week_label: str | None = None,
    threads: list[dict[str, str]] | None = None,
) -> dict[str, str]:
    """Return episode title and description (Chinese) derived from the export Markdown.

    If *threads* is provided, uses them directly instead of re-parsing from markdown.
    """
    label = week_label or current_week_label()
    title = f"【{SERIES_NAME}】{SERIES_ZH} · {label}"

    if threads is None:
        threads = _extract_threads(markdown)
    description = _format_description(threads, label)

    return {
        "title": title,
        "description": description,
        "week_label": label,
        "threads": threads,
    }


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
# File writer
# ---------------------------------------------------------------------------

def write_forum_post(
    markdown_export_path: Path,
    output_path: Path | None = None,
    *,
    audio_url: str | None = None,
    extra_links: dict[str, str] | None = None,
    threads: list[dict[str, str]] | None = None,
) -> Path:
    """Read the exported Markdown, generate an episode reply, write to disk.

    If *threads* is provided, passes them to episode_metadata() directly
    instead of re-parsing the markdown via regex.
    """
    md_path = Path(markdown_export_path).resolve()
    md_content = md_path.read_text(encoding="utf-8")

    meta = episode_metadata(md_content, threads=threads)
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
