#!/usr/bin/env python3
"""Show-specific wrapper around the CastForge pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys

from castforge.pipeline import PipelineHooks, main as castforge_main
from extractor import (
    extract_weekly_key_info,
    fetch_thread_details,
    list_mcp_tools,
    select_threads,
    threads_to_source_markdown,
)
from public_contract import EPISODE_FILE_PREFIX, PUBLIC_AUDIO_BASE_URL, week_episode_filename, week_episode_url
from publisher import write_forum_post
from rss_feed import generate_rss_feed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--topic", type=int, help="Special edition for a specific topic ID")
    parser.add_argument("--category", type=str, help="Special edition for a specific category")

    known, remaining = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    stem = ""
    if known.category:
        os.environ["MCP_EXTRACT_TOOL"] = "discourse_search"
        os.environ["MCP_EXTRACT_TOOL_ARGUMENTS"] = json.dumps({
            "category": known.category,
            "order": "likes",
            "max_results": 7,
        })
        os.environ["EPISODE_LABEL"] = f"专题报道-{known.category}"
        stem = f"special_category_{known.category}"
    elif known.topic:
        os.environ["MCP_EXTRACT_TOOL"] = "discourse_read_topic"
        os.environ["MCP_EXTRACT_TOOL_ARGUMENTS"] = json.dumps({
            "topic_id": known.topic,
            "post_limit": 50,
        })
        os.environ["EPISODE_LABEL"] = f"专题报道-话题{known.topic}"
        stem = f"special_topic_{known.topic}"

    if stem:
        for flag, value in (
            ("--output-filename", f"{stem}.md"),
            ("--notebooklm-audio-out", f"releases/{stem}.mp3"),
            ("--audio-url", f"{PUBLIC_AUDIO_BASE_URL}/{stem}.mp3"),
        ):
            if flag not in remaining:
                remaining.extend([flag, value])

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
    return castforge_main(remaining, hooks=hooks)


if __name__ == "__main__":
    raise SystemExit(main())
