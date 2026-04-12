#!/usr/bin/env python3
"""Show-specific wrapper around the extracted CastForge pipeline."""

from __future__ import annotations

from _castforge import ensure_castforge_on_path

ensure_castforge_on_path()

from castforge.pipeline import PipelineHooks, main as castforge_main
from extractor import (
    extract_weekly_key_info,
    fetch_thread_details,
    list_mcp_tools,
    select_threads,
    threads_to_source_markdown,
)
from public_contract import EPISODE_FILE_PREFIX, week_episode_filename, week_episode_url
from publisher import write_forum_post
from rss_feed import generate_rss_feed


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import os
    import sys

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--topic", type=int, help="Special edition for a specific topic ID")
    parser.add_argument("--category", type=str, help="Special edition for a specific category")
    
    args_to_parse = argv if argv is not None else sys.argv[1:]
    known, remaining = parser.parse_known_args(args_to_parse)

    if known.category:
        os.environ["MCP_EXTRACT_TOOL"] = "discourse_search"
        os.environ["MCP_EXTRACT_TOOL_ARGUMENTS"] = json.dumps({
            "category": known.category,
            "order": "likes",
            "max_results": 7
        })
        os.environ["EPISODE_LABEL"] = f"专题报道-{known.category}"
        if "--output-filename" not in remaining:
            remaining.extend(["--output-filename", f"special_category_{known.category}.md"])
        if "--notebooklm-audio-out" not in remaining:
            remaining.extend(["--notebooklm-audio-out", f"releases/special_category_{known.category}.mp3"])
        if "--audio-url" not in remaining:
            remaining.extend(["--audio-url", f"https://lifan-builds.github.io/nitan-podcast/episodes/special_category_{known.category}.mp3"])
    elif known.topic:
        os.environ["MCP_EXTRACT_TOOL"] = "discourse_read_topic"
        # We also pass the topic_id natively so we can inject the title later
        os.environ["MCP_EXTRACT_TOOL_ARGUMENTS"] = json.dumps({
            "topic_id": known.topic,
            "post_limit": 50
        })
        os.environ["EPISODE_LABEL"] = f"专题报道-话题{known.topic}"
        if "--output-filename" not in remaining:
            remaining.extend(["--output-filename", f"special_topic_{known.topic}.md"])
        if "--notebooklm-audio-out" not in remaining:
            remaining.extend(["--notebooklm-audio-out", f"releases/special_topic_{known.topic}.mp3"])
        if "--audio-url" not in remaining:
            remaining.extend(["--audio-url", f"https://lifan-builds.github.io/nitan-podcast/episodes/special_topic_{known.topic}.mp3"])

    argv = remaining

    hooks = PipelineHooks(
        extract_weekly_key_info=extract_weekly_key_info,
        fetch_thread_details=fetch_thread_details,
        list_mcp_tools=list_mcp_tools,
        select_threads=select_threads,
        threads_to_source_markdown=threads_to_source_markdown,
        write_forum_post=write_forum_post,
        generate_rss_feed=generate_rss_feed,
        episode_file_prefix=EPISODE_FILE_PREFIX,
        week_episode_filename=week_episode_filename,
        week_episode_url=week_episode_url,
    )
    return castforge_main(argv, hooks=hooks)


if __name__ == "__main__":
    raise SystemExit(main())
