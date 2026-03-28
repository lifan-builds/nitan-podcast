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


def threads_to_source_markdown(threads: list[dict[str, Any]]) -> str:
    """Turn structured extraction into a Chinese-friendly NotebookLM source (no LLM)."""
    lines: list[str] = [
        "# 美卡论坛（USCardForum）· 本周热点素材\n\n",
        "> 供 **NotebookLM** 上传为来源。生成 Audio Overview 时请在说明中使用 **中文** 口播。\n\n",
    ]
    for i, t in enumerate(threads, 1):
        lines.append(f"## 线索 {i}\n\n")
        for key, val in t.items():
            if isinstance(val, (dict, list)):
                val_s = json.dumps(val, ensure_ascii=False, indent=2)
            else:
                val_s = str(val)
            lines.append(f"- **{key}**：{val_s}\n")
        lines.append("\n")
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
