"""Unit tests for publisher module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from publisher import (
    SERIES_NAME,
    SERIES_ZH,
    _extract_thread_titles,
    _extract_threads,
    announcement_post_markdown,
    episode_metadata,
    episode_reply_markdown,
    write_announcement_post,
    write_forum_post,
)


# ---------------------------------------------------------------------------
# _extract_threads (regex parsing from markdown)
# ---------------------------------------------------------------------------

class TestExtractThreads:

    def test_extracts_from_source_markdown(self, sample_markdown: str):
        threads = _extract_threads(sample_markdown)
        assert len(threads) == 2
        assert threads[0]["title"] == "示例：某酒店卡史高讨论"
        assert threads[1]["title"] == "示例：羊毛线报"

    def test_extracts_category(self, sample_markdown: str):
        threads = _extract_threads(sample_markdown)
        assert threads[0]["category"] == "信用卡"

    def test_extracts_url(self, sample_markdown: str):
        threads = _extract_threads(sample_markdown)
        assert "uscardforum.com" in threads[0].get("url", "")

    def test_empty_markdown(self):
        assert _extract_threads("") == []

    def test_no_threads_section(self):
        assert _extract_threads("# Just a heading\n\nSome text.") == []

    def test_single_thread(self):
        md = "## 线索 1\n\n- **title**：Test Title\n- **category**：Cat\n"
        threads = _extract_threads(md)
        assert len(threads) == 1
        assert threads[0]["title"] == "Test Title"


class TestExtractThreadTitles:

    def test_returns_titles(self, sample_markdown: str):
        titles = _extract_thread_titles(sample_markdown)
        assert len(titles) == 2
        assert titles[0] == "示例：某酒店卡史高讨论"

    def test_empty_returns_empty(self):
        assert _extract_thread_titles("") == []


# ---------------------------------------------------------------------------
# episode_metadata
# ---------------------------------------------------------------------------

class TestEpisodeMetadata:

    def test_title_format(self, sample_markdown: str):
        meta = episode_metadata(sample_markdown, week_label="2026年第13周")
        assert SERIES_NAME in meta["title"]
        assert SERIES_ZH in meta["title"]
        assert "2026年第13周" in meta["title"]

    def test_description_has_bullets(self, sample_markdown: str):
        meta = episode_metadata(sample_markdown)
        assert "本期话题" in meta["description"]
        assert "示例：某酒店卡史高讨论" in meta["description"]

    def test_threads_in_metadata(self, sample_markdown: str):
        meta = episode_metadata(sample_markdown)
        assert len(meta["threads"]) == 2

    def test_with_prebuilt_threads(self, sample_threads: list[dict[str, Any]]):
        meta = episode_metadata("", threads=sample_threads, week_label="2026年第1周")
        assert "示例：某酒店卡史高讨论" in meta["description"]
        assert len(meta["threads"]) == 2

    def test_fallback_description_no_threads(self):
        meta = episode_metadata("# No threads here", week_label="2026年第1周")
        assert SERIES_ZH in meta["description"]

    def test_prebuilt_threads_skip_regex(self):
        """When threads are passed, markdown content is irrelevant."""
        threads = [{"title": "Direct Thread"}]
        meta = episode_metadata("garbage markdown", threads=threads)
        assert "Direct Thread" in meta["description"]


# ---------------------------------------------------------------------------
# episode_reply_markdown
# ---------------------------------------------------------------------------

class TestEpisodeReplyMarkdown:

    def _meta(self, threads: list[dict[str, Any]]) -> dict[str, str]:
        return episode_metadata("", threads=threads, week_label="2026年第13周")

    def test_header(self, sample_threads: list[dict[str, Any]]):
        post = episode_reply_markdown(self._meta(sample_threads))
        assert f"# {SERIES_ZH}" in post

    def test_audio_url_link(self, sample_threads: list[dict[str, Any]]):
        post = episode_reply_markdown(
            self._meta(sample_threads),
            audio_url="https://example.com/ep.mp3",
        )
        assert "https://example.com/ep.mp3" in post
        assert "收听本期" in post

    def test_discourse_upload_syntax(self, sample_threads: list[dict[str, Any]]):
        post = episode_reply_markdown(
            self._meta(sample_threads),
            audio_url="upload://abc123",
        )
        assert "![" in post
        assert "upload://abc123" in post

    def test_no_audio_shows_hint(self, sample_threads: list[dict[str, Any]]):
        post = episode_reply_markdown(self._meta(sample_threads))
        assert "MP3" in post

    def test_topic_table(self, sample_threads: list[dict[str, Any]]):
        post = episode_reply_markdown(self._meta(sample_threads))
        assert "| # |" in post
        assert "示例：某酒店卡史高讨论" in post
        assert "信用卡" in post

    def test_extra_links(self, sample_threads: list[dict[str, Any]]):
        post = episode_reply_markdown(
            self._meta(sample_threads),
            extra_links={"Spotify": "https://spotify.com/show/123"},
        )
        assert "Spotify" in post
        assert "其他平台" in post


# ---------------------------------------------------------------------------
# announcement_post_markdown
# ---------------------------------------------------------------------------

class TestAnnouncementPost:

    def test_contains_series_name(self):
        post = announcement_post_markdown()
        assert SERIES_NAME in post

    def test_contains_faq(self):
        post = announcement_post_markdown()
        assert "FAQ" in post

    def test_contains_tech_stack(self):
        post = announcement_post_markdown()
        assert "Nitan MCP" in post


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------

class TestWriteForumPost:

    def test_writes_file(self, tmp_path: Path, sample_markdown: str):
        from notebooklm_export import export_for_notebooklm
        md_path = export_for_notebooklm(sample_markdown, export_dir=tmp_path, filename="test.md")
        post_path = write_forum_post(md_path)
        assert post_path.is_file()
        content = post_path.read_text(encoding="utf-8")
        assert SERIES_ZH in content

    def test_with_prebuilt_threads(self, tmp_path: Path, sample_threads: list[dict[str, Any]]):
        from notebooklm_export import export_for_notebooklm
        md_path = export_for_notebooklm("# test", export_dir=tmp_path, filename="test.md")
        post_path = write_forum_post(md_path, threads=sample_threads)
        content = post_path.read_text(encoding="utf-8")
        assert "示例：某酒店卡史高讨论" in content

    def test_custom_output_path(self, tmp_path: Path, sample_markdown: str):
        from notebooklm_export import export_for_notebooklm
        md_path = export_for_notebooklm(sample_markdown, export_dir=tmp_path, filename="test.md")
        out = tmp_path / "custom_post.md"
        post_path = write_forum_post(md_path, output_path=out)
        assert post_path == out.resolve()


class TestWriteAnnouncementPost:

    def test_writes_file(self, tmp_path: Path):
        out = tmp_path / "announce.md"
        path = write_announcement_post(out)
        assert path.is_file()
        assert SERIES_NAME in path.read_text(encoding="utf-8")
