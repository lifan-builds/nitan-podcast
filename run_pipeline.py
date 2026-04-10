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
