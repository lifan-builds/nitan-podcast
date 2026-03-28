#!/usr/bin/env python3
"""
Weekly-job-friendly orchestrator: MCP extract → optional Gemini briefing → Markdown export;
optional ``--publish-notebooklm`` uploads to NotebookLM (notebooklm-py) and downloads Audio Overview.

Exit 0 on success, 1 on failure. Logs to stderr. No interactive prompts.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from briefing_writer import write_briefing_markdown
from extractor import extract_weekly_key_info, list_mcp_tools, threads_to_source_markdown
from notebooklm_export import DEFAULT_EXPORT_DIR, DEFAULT_MARKDOWN_NAME, export_for_notebooklm
from publisher import write_forum_post

DEFAULT_RELEASES_DIR = Path("releases")


def _week_filename(prefix: str = "weekly_meika", ext: str = ".md") -> str:
    iso = date.today().isocalendar()
    return f"{prefix}_{iso.year}-W{iso.week:02d}{ext}"


def _default_audio_out(dated: bool) -> Path:
    iso = date.today().isocalendar()
    name = f"weekly_meika_{iso.year}-W{iso.week:02d}.mp3" if dated else "weekly_meika_podcast.mp3"
    return (DEFAULT_RELEASES_DIR / name).resolve()


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="USCardForum → NotebookLM Markdown export pipeline")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Dotenv path (default: .env)",
    )
    parser.add_argument("--skip-briefing", action="store_true", help="Skip Gemini; export structured Markdown from extraction only")
    parser.add_argument("--export-dir", type=Path, default=None, help=f"Export directory (default: {DEFAULT_EXPORT_DIR})")
    parser.add_argument(
        "--output-filename",
        default=None,
        help=f"Output filename (default: {DEFAULT_MARKDOWN_NAME} or ISO-week name if --dated)",
    )
    parser.add_argument("--dated", action="store_true", help="Use ISO week filename weekly_meika_YYYY-Www.md")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument(
        "--list-mcp-tools",
        action="store_true",
        help="Connect to MCP server, print tool names/schemas as JSON, exit",
    )
    parser.add_argument(
        "--publish-notebooklm",
        action="store_true",
        help="After export: upload Markdown to NotebookLM, generate Audio Overview, download MP3 (requires notebooklm-py + notebooklm login)",
    )
    parser.add_argument(
        "--notebooklm-audio-out",
        type=Path,
        default=None,
        help="Path for downloaded audio (default: releases/weekly_meika_YYYY-Www.mp3 if --dated else releases/weekly_meika_podcast.mp3)",
    )
    parser.add_argument(
        "--publish-soundcloud",
        action="store_true",
        help="Upload MP3 to SoundCloud (requires soundcloud_upload.py login + SOUNDCLOUD_CLIENT_ID)",
    )
    parser.add_argument(
        "--generate-post",
        action="store_true",
        help="Generate a 美卡论坛 Discourse post (Markdown) alongside the export",
    )
    parser.add_argument(
        "--audio-url",
        default=None,
        help="Podcast episode URL to embed in the forum post and RSS feed",
    )
    parser.add_argument(
        "--generate-rss",
        action="store_true",
        help="Generate/update podcast RSS feed (docs/feed.xml) for Apple Podcasts / Spotify / 小宇宙",
    )
    parser.add_argument(
        "--rss-output",
        type=Path,
        default=None,
        help="Path for RSS feed file (default: docs/feed.xml)",
    )
    parser.add_argument(
        "--episode-duration",
        default="00:06:00",
        help="Episode duration as HH:MM:SS for RSS feed (default: 00:06:00)",
    )
    args = parser.parse_args(argv)

    _setup_logging(args.log_level)
    log = logging.getLogger("run_pipeline")

    if args.env_file.is_file():
        load_dotenv(args.env_file, override=False)
    else:
        load_dotenv(override=False)

    if args.list_mcp_tools:
        try:
            tools = list_mcp_tools()
            out = [
                {
                    "name": t.name,
                    "description": getattr(t, "description", None),
                    "inputSchema": getattr(t, "inputSchema", None),
                }
                for t in tools
            ]
            json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
            return 0
        except Exception:
            log.exception("Failed to list MCP tools")
            return 1

    export_dir = args.export_dir if args.export_dir is not None else DEFAULT_EXPORT_DIR
    if args.output_filename:
        filename = args.output_filename
    elif args.dated:
        filename = _week_filename()
    else:
        filename = DEFAULT_MARKDOWN_NAME

    try:
        threads = extract_weekly_key_info()
        if not threads:
            log.error("Extraction returned no threads")
            return 1

        raw_md = threads_to_source_markdown(threads)

        if args.skip_briefing:
            body = raw_md
            log.info("Skipping Gemini briefing")
        else:
            body = write_briefing_markdown(raw_md)

        path = export_for_notebooklm(body, export_dir=export_dir, filename=filename)
        log.info("Wrote NotebookLM source: %s", path)

        audio_path = None

        if args.publish_notebooklm:
            from notebooklm_audio import publish_weekly_audio

            audio_path = args.notebooklm_audio_out
            if audio_path is None:
                audio_path = _default_audio_out(args.dated)
            else:
                audio_path = audio_path.resolve()
            log.info("Publishing to NotebookLM; audio output: %s", audio_path)
            publish_weekly_audio(path, audio_path)
            log.info("Downloaded Audio Overview: %s", audio_path)

        # SoundCloud upload (after we have an MP3)
        soundcloud_url = args.audio_url
        if args.publish_soundcloud and audio_path and audio_path.is_file():
            from publisher import current_week_label
            from soundcloud_upload import upload_episode

            week_label = current_week_label()
            log.info("Uploading to SoundCloud...")
            soundcloud_url = upload_episode(audio_path, week_label)
            log.info("SoundCloud URL: %s", soundcloud_url)

        # Forum post (uses SoundCloud URL if available)
        if args.generate_post:
            post_path = write_forum_post(path, audio_url=soundcloud_url)
            log.info("Wrote forum post: %s", post_path)

        # RSS feed
        if args.generate_rss:
            from rss_feed import generate_rss_feed

            rss_audio_url = soundcloud_url or args.audio_url
            if not rss_audio_url:
                iso = date.today().isocalendar()
                rss_audio_url = (
                    f"https://github.com/lifan-builds/nitan-podcast/releases/"
                    f"download/v{iso.year}-W{iso.week:02d}/"
                    f"weekly_meika_{iso.year}-W{iso.week:02d}.mp3"
                )
            feed_path = generate_rss_feed(
                path,
                args.rss_output,
                audio_url=rss_audio_url,
                duration=args.episode_duration,
            )
            log.info("Updated RSS feed: %s", feed_path)

        if audio_path and audio_path.is_file():
            print(str(audio_path), file=sys.stdout)
        else:
            print(str(path), file=sys.stdout)
        return 0
    except Exception:
        log.exception("Pipeline failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
