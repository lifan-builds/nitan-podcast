"""
MCP client for nitan-MCP: fetch weekly top/trending uscardforum.com content.

Configure via environment (see `.env.example`). Tool name and arguments are
server-specific — use `run_pipeline.py --list-mcp-tools` after pointing
`MCP_SERVER_COMMAND` at nitan-MCP.

Output is **key information** as `list[dict]` for NotebookLM-oriented Markdown.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import anyio
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, get_default_environment, stdio_client

logger = logging.getLogger(__name__)

ENV_COMMAND = "MCP_SERVER_COMMAND"
ENV_ARGS = "MCP_SERVER_ARGS"
ENV_TOOL = "MCP_EXTRACT_TOOL"
ENV_TOOL_ARGS = "MCP_EXTRACT_TOOL_ARGUMENTS"
ENV_SERVER_ENV = "MCP_SERVER_ENV_JSON"
ENV_FIXTURE = "EXTRACTION_FIXTURE_PATH"
ENV_DETAIL_TOOL = "MCP_DETAIL_TOOL"
ENV_DETAIL_POST_LIMIT = "MCP_DETAIL_POST_LIMIT"
DEFAULT_DETAIL_TOOL = "discourse_read_topic"
DEFAULT_DETAIL_POST_LIMIT = 50  # fetch deeper so substance can beat low-info reactions
MAX_OP_CHARS = 2200
MAX_REPLY_CHARS = 700
MAX_INFORMATIVE_REPLIES = 8
CATEGORY_VOICE_PATH = Path(__file__).resolve().parent / "editorial" / "category_voice.yaml"


def _parse_json_list(raw: str | None) -> list[str]:
    if not raw or not raw.strip():
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("MCP_SERVER_ARGS must be a JSON array of strings")
    return [str(x) for x in data]


def _parse_tool_arguments(raw: str | None) -> dict[str, Any]:
    if not raw or not raw.strip():
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("MCP_EXTRACT_TOOL_ARGUMENTS must be a JSON object")
    return data


def _detail_post_limit() -> int:
    raw = os.environ.get(ENV_DETAIL_POST_LIMIT, "").strip()
    if not raw:
        return DEFAULT_DETAIL_POST_LIMIT
    try:
        value = int(raw)
    except ValueError as e:
        raise ValueError(f"{ENV_DETAIL_POST_LIMIT} must be an integer") from e
    return max(1, value)


def _merge_process_env() -> dict[str, str]:
    base = get_default_environment()
    base.update(dict(os.environ))
    return base


def _stdio_params() -> StdioServerParameters:
    command = os.environ.get(ENV_COMMAND, "").strip()
    if not command:
        raise RuntimeError(
            f"Set {ENV_COMMAND} to the nitan-MCP executable (e.g. path to binary or `uvx`). "
            f"For CI demos without a server, set {ENV_FIXTURE} to a JSON file path instead."
        )
    args = _parse_json_list(os.environ.get(ENV_ARGS))
    extra_env: dict[str, str] | None
    raw_se = os.environ.get(ENV_SERVER_ENV, "").strip()
    if raw_se:
        parsed = json.loads(raw_se)
        if not isinstance(parsed, dict):
            raise ValueError("MCP_SERVER_ENV_JSON must be a JSON object of string values")
        merged = _merge_process_env()
        merged.update({str(k): str(v) for k, v in parsed.items()})
        extra_env = merged
    else:
        extra_env = _merge_process_env()
    return StdioServerParameters(command=command, args=args, env=extra_env)


def _load_fixture() -> list[dict[str, Any]] | None:
    path = os.environ.get(ENV_FIXTURE, "").strip()
    if not path:
        return None
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"{ENV_FIXTURE}: not a file: {path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if "threads" in data and isinstance(data["threads"], list):
            return [x for x in data["threads"] if isinstance(x, dict)]
        return [data]
    raise ValueError(f"{ENV_FIXTURE}: JSON must be a list of objects or a single object")


def _unwrap_dict_or_list(data: Any) -> list[dict[str, Any]]:
    """Extract a list of dicts from a raw JSON value (list, dict with known keys, or single dict)."""
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("threads", "posts", "items", "data"):
            inner = data.get(key)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
        return [data]
    return []


def tool_result_to_threads(result: types.CallToolResult) -> list[dict[str, Any]]:
    if result.isError:
        parts = []
        for block in result.content:
            if isinstance(block, types.TextContent):
                parts.append(block.text)
        raise RuntimeError("MCP tool returned isError=true: " + (" ".join(parts) or "(no text)"))

    if result.structuredContent is not None:
        return _unwrap_dict_or_list(result.structuredContent)

    texts: list[str] = []
    for block in result.content:
        if isinstance(block, types.TextContent):
            texts.append(block.text)
    raw = "\n".join(texts).strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return _unwrap_dict_or_list(data)
    except json.JSONDecodeError:
        pass
        
    tool_name = os.environ.get(ENV_TOOL, "").strip()
    if tool_name == "discourse_read_topic":
        args = _parse_tool_arguments(os.environ.get(ENV_TOOL_ARGS))
        topic_id = args.get("topic_id", "")
        return [{"title": f"本期专题：话题 {topic_id}", "url": f"https://www.uscardforum.com/t/topic/{topic_id}", "category": "专题报道", "raw_text": raw}]

    return [{"title": "forum_digest", "raw_text": raw}]


async def extract_weekly_key_info_async() -> list[dict[str, Any]]:
    fixture = _load_fixture()
    if fixture is not None:
        logger.info("Loaded %s thread(s) from %s", len(fixture), ENV_FIXTURE)
        return fixture

    tool_name = os.environ.get(ENV_TOOL, "").strip()
    if not tool_name:
        raise RuntimeError(
            f"Set {ENV_TOOL} to the MCP tool name that returns weekly forum data "
            f"(discover names with: python run_pipeline.py --list-mcp-tools)."
        )
    tool_args = _parse_tool_arguments(os.environ.get(ENV_TOOL_ARGS))
    params = _stdio_params()

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, tool_args)
            threads = tool_result_to_threads(result)
            logger.info("MCP tool %r returned %s thread record(s)", tool_name, len(threads))
            return threads


def extract_weekly_key_info() -> list[dict[str, Any]]:
    """Sync entrypoint for orchestrator and jobs."""
    return anyio.run(extract_weekly_key_info_async)


# ---------------------------------------------------------------------------
# Thread detail fetching (replies / comments)
# ---------------------------------------------------------------------------

def _extract_topic_id(thread: dict[str, Any]) -> int | None:
    """Try to extract topic_id from thread dict (id field or URL)."""
    if "id" in thread:
        try:
            return int(thread["id"])
        except (ValueError, TypeError):
            pass
    url = thread.get("url", "")
    # Pattern: /t/topic/493110 or /t/slug/493110
    import re
    m = re.search(r"/t/[^/]+/(\d+)", url)
    if m:
        return int(m.group(1))
    return None


def _parse_topic_text(text: str) -> list[dict[str, Any]]:
    """Parse the text-format response from discourse_read_topic into a list of post dicts.

    Format: ``- Post #N by @username (date)\\n  content...``
    """
    posts: list[dict[str, Any]] = []
    # Split on post markers
    parts = re.split(r"^- Post #(\d+) by @(\S+) \(([^)]+)\)", text, flags=re.MULTILINE)
    # parts[0] is the header before the first post
    # Then groups of 4: post_num, username, date, content
    i = 1
    while i + 3 <= len(parts):
        post_num = int(parts[i])
        username = parts[i + 1]
        post_date = parts[i + 2]
        content = parts[i + 3].strip()
        # Remove trailing "Link: ..." line
        content = re.sub(r"\nLink: https?://\S+\s*$", "", content).strip()
        # Remove image upload references
        content = re.sub(r"!\[[^\]]*\]\([^)]+\)\s*", "", content).strip()
        posts.append({
            "post_num": post_num,
            "username": username,
            "date": post_date,
            "text": content,
        })
        i += 4
    return posts


_POSITIVE_INFO_PATTERNS = [
    r"\bDP\b",
    r"\bTL;?DR\b",
    r"\bYMMV\b",
    r"\bupdate\b",
    r"\bdata\b",
    r"\blink\b",
    r"\bsource\b",
    r"\bAmex\b",
    r"\bChase\b",
    r"\bCiti\b",
    r"\bCapital\s*One\b",
    r"\bWF\b",
    r"\bBilt\b",
    r"\bCSR\b",
    r"\bMR\b",
    r"\bUR\b",
    r"\bCX\b",
    r"\bHyatt\b",
    r"\bUA\b",
    r"\bAA\b",
    r"\bAS\b",
    r"\b5/24\b",
    r"\b\d+(?:\.\d+)?\s*(?:%|x|X|cpp|刀|块|美元|points?|miles?|pts?)\b",
    r"\b20\d{2}[-/年]\d{1,2}",
    r"\d{1,2}[/-]\d{1,2}",
    r"实测|亲测|数据点|补充|更正|纠正|不是|其实|准确|条款|链接|来源|官方|公告|邮件|客服|截图|日期|时间|金额|比例|转点|报销|年费|风险|限制|过期|失效|成功|失败|可用|不可用|坐标|地区|航线|酒店|账户|税|身份|签证|面试|offer|收入|资产|本金|收益|亏损|假设|重点|建议|提醒|背景|影响|适合|不适合|专业|律师|现金流|H1B|therapist|EAP",
]

_REACTION_ONLY_PATTERNS = [
    r"^[\W_]*$",
    r"^(牛+|笑死|哈哈+|哈哈哈+|支持|蹲|马克|mark|顶|关注|学习了|感谢分享|好帖|同意|确实|离谱|绷不住|东直门|东便门|恭喜|太惨了)[\W_]*$",
    r"^(\+1|1|cy|插眼|前排)[\W_]*$",
]

_LOW_INFO_COLOR_PATTERNS = [
    r"恭喜楼主|太好看|好看了|拍不出|不是那么扫兴",
    r":joy:|:rofl:|:troll:|:ghost:",
]


def _clean_reply_text(reply: dict[str, Any]) -> str:
    text = str(reply.get("text", reply.get("raw", reply.get("cooked", ""))) or "")
    if "<" in text:
        text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[quote=.*?\].*?\[/quote\]", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"https?://\S+", lambda m: m.group(0).rstrip(".,)"), text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_REPLY_CHARS:
        text = text[: MAX_REPLY_CHARS - 3].rstrip() + "..."
    return text


def _information_score(text: str, reply: dict[str, Any] | None = None) -> float:
    """Score whether a reply adds usable information rather than only color."""
    normalized = text.strip()
    if not normalized:
        return 0
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in _REACTION_ONLY_PATTERNS):
        return 0
    if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in _LOW_INFO_COLOR_PATTERNS):
        score_penalty = 4.0
    else:
        score_penalty = 0.0

    score = 0.0
    length = len(normalized)
    if length >= 40:
        score += 1
    if length >= 120:
        score += 1
    if length >= 240:
        score += 1

    for pattern in _POSITIVE_INFO_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            score += 2

    if re.search(r"\d", normalized):
        score += 1
    if any(mark in normalized for mark in ("：", ":", "；", ";", "，", ",")):
        score += 0.5

    if reply:
        try:
            likes = int(reply.get("likes", reply.get("like_count", 0)) or 0)
        except (TypeError, ValueError):
            likes = 0
        score += min(likes, 20) * 0.05

    return score - score_penalty


def _pick_informative_replies(
    posts: list[dict[str, Any]],
    max_replies: int = MAX_INFORMATIVE_REPLIES,
) -> list[str]:
    """Select replies that add facts, data points, corrections, or constraints."""
    if len(posts) <= 1:
        return []

    replies = posts[1:]  # skip OP
    scored: list[tuple[float, int, str]] = []
    for idx, reply in enumerate(replies):
        text = _clean_reply_text(reply)
        score = _information_score(text, reply)
        if score < 2:
            continue
        scored.append((score, idx, text))

    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    selected = sorted(scored[:max_replies], key=lambda item: item[1])
    picked: list[str] = []
    seen: set[str] = set()
    for _, _, text in selected:
        dedupe_key = text[:80]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        picked.append(text)
    return picked


def _enrich_thread(thread: dict[str, Any], posts: list[dict[str, Any]]) -> dict[str, Any]:
    """Merge reply data into the thread dict."""
    enriched = dict(thread)
    if not posts:
        return enriched

    # OP content (first post)
    op_text = posts[0].get("text", "")
    if len(op_text) > MAX_OP_CHARS:
        op_text = op_text[: MAX_OP_CHARS - 3].rstrip() + "..."
    if op_text:
        enriched["op_content"] = op_text.strip()

    informative_replies = _pick_informative_replies(posts)
    if informative_replies:
        enriched["informative_replies"] = informative_replies

    # Reply count
    enriched["reply_count"] = len(posts) - 1 if len(posts) > 1 else 0
    return enriched


async def fetch_thread_details_async(
    threads: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fetch detail (posts/replies) for each thread via MCP and enrich them.

    Uses a single MCP session for all calls. If MCP_DETAIL_TOOL is unset,
    falls back to DEFAULT_DETAIL_TOOL. Errors on individual threads are
    logged and skipped (the thread is returned un-enriched).
    """
    detail_tool = os.environ.get(ENV_DETAIL_TOOL, "").strip() or DEFAULT_DETAIL_TOOL

    # Collect topic IDs
    topics = [(i, _extract_topic_id(t)) for i, t in enumerate(threads)]
    valid_topics = [(i, tid) for i, tid in topics if tid is not None]
    if not valid_topics:
        logger.warning("No topic IDs found in threads; skipping detail fetch")
        return threads

    fixture = _load_fixture()
    if fixture is not None:
        # In fixture mode, threads already have whatever data the fixture provides
        logger.info("Fixture mode: skipping MCP detail fetch")
        return threads

    params = _stdio_params()
    enriched = list(threads)  # copy

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for idx, topic_id in valid_topics:
                try:
                    result = await session.call_tool(
                        detail_tool,
                        {"topic_id": topic_id, "post_limit": _detail_post_limit()},
                    )
                    # discourse_read_topic returns text, not structured JSON
                    raw_text = ""
                    for block in result.content:
                        if isinstance(block, types.TextContent):
                            raw_text += block.text
                    posts = _parse_topic_text(raw_text)
                    enriched[idx] = _enrich_thread(threads[idx], posts)
                    logger.info(
                        "Fetched %d posts for topic %d (%s)",
                        len(posts), topic_id, threads[idx].get("title", "?")[:30],
                    )
                except Exception:
                    logger.warning("Failed to fetch details for topic %d; skipping", topic_id, exc_info=True)

    return enriched


def fetch_thread_details(threads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sync entrypoint for thread detail enrichment."""
    return anyio.run(fetch_thread_details_async, threads)


def select_threads(
    threads: list[dict[str, Any]],
    max_count: int = 7,
    max_per_category: int = 3,
) -> list[dict[str, Any]]:
    """Score and select diverse threads from a larger pool.

    Scoring combines likes, views, and reply count. Category diversity is
    enforced by capping per-category selections.
    """
    if len(threads) <= max_count:
        return threads

    def _score(t: dict[str, Any]) -> float:
        likes = t.get("like_count", t.get("likes", 0)) or 0
        views = t.get("views", 0) or 0
        posts = t.get("posts_count", t.get("reply_count", 0)) or 0
        # Weighted composite: likes matter most, views secondary, posts for controversy
        return likes * 3 + views * 0.01 + posts * 2

    scored = sorted(threads, key=_score, reverse=True)

    selected: list[dict[str, Any]] = []
    cat_counts: dict[str, int] = {}

    for t in scored:
        if len(selected) >= max_count:
            break
        cat = t.get("category", "其他")
        if cat_counts.get(cat, 0) >= max_per_category:
            continue
        selected.append(t)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # If we didn't fill up due to category caps, relax caps and add remaining
    if len(selected) < max_count:
        relaxed_max = max_per_category + 1
        for t in scored:
            if len(selected) >= max_count:
                break
            if t not in selected:
                cat = t.get("category", "其他")
                if cat_counts.get(cat, 0) < relaxed_max:
                    selected.append(t)
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1

    return selected


def _load_category_voice_guide(path: Path = CATEGORY_VOICE_PATH) -> dict[str, Any]:
    if not path.is_file():
        return {
            "default": {
                "voice": "fact-first, conversational, lightly witty",
                "lead_with": ["what happened", "why it matters", "what the community disagrees about"],
                "avoid": ["opening with jokes before context"],
            },
            "categories": {},
        }

    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Category voice guide must be a YAML object: {path}")
    data.setdefault("default", {})
    data.setdefault("categories", {})
    return data


def _category_voice(category: str, guide: dict[str, Any]) -> dict[str, Any]:
    categories = guide.get("categories", {})
    if not isinstance(categories, dict):
        categories = {}
    default = guide.get("default", {})
    if not isinstance(default, dict):
        default = {}
    category_note = categories.get(category, {})
    if not isinstance(category_note, dict):
        category_note = {}
    merged = dict(default)
    merged.update(category_note)
    return merged


def _format_value(val: Any) -> str:
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False, indent=2)
    return str(val)


def _render_voice_note(voice: dict[str, Any]) -> str:
    lines: list[str] = []
    if voice.get("voice"):
        lines.append(f"- voice: {voice['voice']}")
    for key, label in (("lead_with", "lead with"), ("avoid", "avoid")):
        values = voice.get(key)
        if isinstance(values, list) and values:
            lines.append(f"- {label}: {', '.join(str(v) for v in values)}")
    return "\n".join(lines) if lines else "- voice: fact-first and source-grounded"


def _first_present(thread: dict[str, Any], keys: tuple[str, ...], max_chars: int | None = None) -> str:
    for key in keys:
        value = thread.get(key)
        if value:
            text = _format_value(value)
            if max_chars is not None and len(text) > max_chars:
                return text[: max_chars - 3].rstrip() + "..."
            return text
    return ""


def _render_essential_context(thread: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    category = thread.get("category")
    if category:
        lines.append(f"- Category: {category}")
    url = thread.get("url")
    if url:
        lines.append(f"- Source URL: {url}")
    stats: list[str] = []
    for key, label in (("like_count", "likes"), ("likes", "likes"), ("views", "views"), ("posts_count", "posts"), ("reply_count", "fetched replies")):
        value = thread.get(key)
        if value not in (None, ""):
            stats.append(f"{label}={value}")
    if stats:
        lines.append(f"- Available stats: {', '.join(stats)}")
    if not lines:
        lines.append("- No category, URL, or engagement metadata was provided by the extractor.")
    return lines


def threads_to_source_markdown(threads: list[dict[str, Any]]) -> str:
    """Turn structured extraction into a Chinese-friendly NotebookLM source (no LLM)."""
    guide = _load_category_voice_guide()
    default_voice = guide.get("default", {})
    lines: list[str] = [
        "# 美卡论坛（USCardForum）· 本周热点素材\n\n",
        "> 供 **NotebookLM** 上传为来源。生成 Audio Overview 时请使用 **中文** 口播。\n",
        "> Each thread below is a fact-first Story Brief. Establish the facts before commentary or banter.\n\n",
        "## Default Editorial Voice\n\n",
        _render_voice_note(default_voice),
        "\n\n",
    ]
    # Keys to render as top-level metadata (skip enriched fields handled separately)
    _ENRICHED_KEYS = {"op_content", "informative_replies", "top_replies", "reply_count"}

    for i, t in enumerate(threads, 1):
        title = str(t.get("title", f"Untitled Thread {i}"))
        category = str(t.get("category", "其他"))
        voice = _category_voice(category, guide)

        lines.append(f"## Story Brief {i}: {title}\n\n")

        lines.append("### What Happened\n\n")
        summary = _first_present(t, ("op_summary", "summary", "blurb", "excerpt", "raw_text", "op_content"), max_chars=700)
        if summary:
            lines.append(f"{summary}\n\n")
        else:
            lines.append(f"Source thread title: {title}\n\n")

        lines.append("### Essential Context\n\n")
        lines.extend(f"{line}\n" for line in _render_essential_context(t))
        lines.append("\n")

        lines.append("### Evidence From Source\n\n")
        for key, val in t.items():
            if key in _ENRICHED_KEYS:
                continue
            val_s = _format_value(val)
            lines.append(f"- **{key}**：{val_s}\n")

        if "op_content" in t:
            lines.append(f"- **op_content**：{t['op_content']}\n")
        lines.append("\n")

        informative = t.get("informative_replies") or []
        if not informative and t.get("top_replies"):
            informative = [
                r.get("text", "") if isinstance(r, dict) else str(r)
                for r in t.get("top_replies", [])
            ]
        lines.append("### Informative Replies\n\n")
        if informative:
            reply_count = t.get("reply_count", len(informative))
            lines.append(f"Fetched discussion count: {reply_count}. Information-bearing replies:\n")
            for reply in informative:
                lines.append(f"- {reply}\n")
        else:
            lines.append("- No information-bearing replies were extracted. Do not infer community consensus from reactions alone.\n")
        lines.append("\n")

        lines.append("### Caveats / Unknowns\n\n")
        if informative:
            lines.append("- Treat replies as source claims or data points, not verified external facts unless the source provides proof.\n")
        else:
            lines.append("- The extractor did not find substantive replies, so the segment should stay close to OP-provided facts.\n")
        lines.append("- If necessary background is missing from the source, say that it is missing instead of filling it in.\n\n")

        lines.append("### Podcast Angle\n\n")
        lines.append("Open with the factual setup, then explain why this thread mattered to the forum. Use replies for substance, corrections, or disagreement after the setup is clear.\n\n")

        lines.append("### Editorial Voice\n\n")
        lines.append(_render_voice_note(voice))

        lines.append("\n\n")
    return "".join(lines)


async def list_mcp_tools_async() -> list[types.Tool]:
    params = _stdio_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            res = await session.list_tools()
            return list(res.tools)


def list_mcp_tools() -> list[types.Tool]:
    return anyio.run(list_mcp_tools_async)
