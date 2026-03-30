"""Unit tests for rss_feed module."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import pytest

from publisher import episode_guid

SAMPLE_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "sample_extraction.json"
from rss_feed import (
    ATOM_NS,
    DEFAULT_FEED_PATH,
    ITUNES_NS,
    _build_channel,
    _build_item,
    _load_existing_items,
    _podcast_config,
    generate_rss_feed,
)


# ---------------------------------------------------------------------------
# publisher.episode_guid
# ---------------------------------------------------------------------------

class TestEpisodeGuid:

    def test_standard_week_label(self):
        assert episode_guid("2026年第13周") == "nitan-podcast-2026-W13"

    def test_single_digit_week(self):
        assert episode_guid("2026年第3周") == "nitan-podcast-2026-W03"

    def test_fallback_for_unexpected_format(self):
        assert episode_guid("custom-label") == "nitan-podcast-custom-label"


# ---------------------------------------------------------------------------
# _build_channel
# ---------------------------------------------------------------------------

class TestBuildChannel:

    def test_required_channel_tags(self):
        config = _podcast_config()
        rss, channel = _build_channel(config)
        assert rss.tag == "rss"
        assert rss.get("version") == "2.0"
        assert channel.find("title") is not None
        assert channel.find("link") is not None
        assert channel.find("description") is not None
        assert channel.find("language") is not None

    def test_itunes_tags_present(self):
        config = _podcast_config()
        _, channel = _build_channel(config)
        ns = {"itunes": ITUNES_NS}
        assert channel.find("itunes:author", ns) is not None
        assert channel.find("itunes:type", ns) is not None
        assert channel.find("itunes:explicit", ns) is not None
        assert channel.find("itunes:owner", ns) is not None
        assert channel.find("itunes:category", ns) is not None

    def test_atom_self_link(self):
        config = _podcast_config()
        _, channel = _build_channel(config)
        atom_link = channel.find(f"{{{ATOM_NS}}}link")
        assert atom_link is not None
        assert atom_link.get("rel") == "self"

    def test_type_is_episodic(self):
        config = _podcast_config()
        _, channel = _build_channel(config)
        ns = {"itunes": ITUNES_NS}
        assert channel.find("itunes:type", ns).text == "episodic"

    def test_category_uses_text_attribute(self):
        """Spotify requires <itunes:category text='X'/>, not <itunes:category>X</itunes:category>."""
        config = _podcast_config()
        _, channel = _build_channel(config)
        ns = {"itunes": ITUNES_NS}
        cat = channel.find("itunes:category", ns)
        assert cat.get("text") == config["category"]
        assert cat.text is None


# ---------------------------------------------------------------------------
# _build_item
# ---------------------------------------------------------------------------

class TestBuildItem:

    def _make_item(self, **kwargs):
        defaults = {
            "title": "Test Episode",
            "description": "Test description",
            "audio_url": "https://example.com/test.mp3",
            "guid": "nitan-podcast-2026-W13",
            "pub_date": datetime(2026, 3, 27, tzinfo=timezone.utc),
            "duration": "00:06:00",
            "file_size": 12345,
        }
        defaults.update(kwargs)
        return _build_item(**defaults)

    def test_required_tags(self):
        item = self._make_item()
        assert item.find("title").text == "Test Episode"
        assert item.find("description").text == "Test description"
        assert item.find("guid").text == "nitan-podcast-2026-W13"
        assert item.find("pubDate") is not None

    def test_enclosure(self):
        item = self._make_item()
        enc = item.find("enclosure")
        assert enc is not None
        assert enc.get("url") == "https://example.com/test.mp3"
        assert enc.get("type") == "audio/mpeg"
        assert enc.get("length") == "12345"

    def test_itunes_duration(self):
        item = self._make_item()
        ns = {"itunes": ITUNES_NS}
        assert item.find("itunes:duration", ns).text == "00:06:00"

    def test_guid_not_permalink(self):
        item = self._make_item()
        assert item.find("guid").get("isPermaLink") == "false"

    def test_pubdate_rfc2822(self):
        item = self._make_item()
        pub = item.find("pubDate").text
        assert "2026" in pub
        assert "GMT" in pub


# ---------------------------------------------------------------------------
# Feed persistence
# ---------------------------------------------------------------------------

class TestFeedPersistence:

    def test_load_nonexistent_returns_empty(self, tmp_path: Path):
        assert _load_existing_items(tmp_path / "nope.xml") == []

    def test_load_invalid_xml_returns_empty(self, tmp_path: Path):
        bad = tmp_path / "bad.xml"
        bad.write_text("not xml at all", encoding="utf-8")
        assert _load_existing_items(bad) == []

    def test_roundtrip_items(self, tmp_path: Path):
        """Write a feed, reload items, verify count."""
        feed = tmp_path / "feed.xml"
        config = _podcast_config()
        rss, channel = _build_channel(config)
        item = _build_item(
            title="Ep1", description="Desc", audio_url="https://x.com/a.mp3",
            guid="guid-1", pub_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        channel.append(item)
        ET.indent(rss)
        ET.ElementTree(rss).write(feed, xml_declaration=True, encoding="unicode")
        items = _load_existing_items(feed)
        assert len(items) == 1
        assert items[0].find("guid").text == "guid-1"


# ---------------------------------------------------------------------------
# generate_rss_feed (integration)
# ---------------------------------------------------------------------------

class TestGenerateRssFeed:

    def _run_generate(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **kwargs):
        from extractor import _load_fixture, threads_to_source_markdown
        from notebooklm_export import export_for_notebooklm

        monkeypatch.setenv("EXTRACTION_FIXTURE_PATH", str(SAMPLE_FIXTURE))
        threads = _load_fixture()
        md = threads_to_source_markdown(threads)
        md_path = export_for_notebooklm(md, export_dir=tmp_path, filename="test.md")

        feed_path = tmp_path / "feed.xml"
        defaults = {
            "audio_url": "https://example.com/episode.mp3",
            "duration": "00:06:00",
        }
        defaults.update(kwargs)
        return generate_rss_feed(md_path, feed_path, **defaults)

    def test_creates_feed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        result = self._run_generate(tmp_path, monkeypatch)
        assert result.is_file()
        content = result.read_text(encoding="utf-8")
        assert "<rss" in content
        assert "<item>" in content
        assert "example.com/episode.mp3" in content

    def test_upsert_idempotent(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        self._run_generate(tmp_path, monkeypatch)
        self._run_generate(tmp_path, monkeypatch)  # same GUID
        feed = tmp_path / "feed.xml"
        tree = ET.parse(feed)
        items = tree.findall(".//item")
        assert len(items) == 1

    def test_different_episodes_accumulate(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # First episode
        self._run_generate(tmp_path, monkeypatch)

        # Manually add a second item with different GUID to simulate a prior week
        feed = tmp_path / "feed.xml"
        tree = ET.parse(feed)
        channel = tree.find("channel")
        old_item = _build_item(
            title="Old Ep", description="Old", audio_url="https://x.com/old.mp3",
            guid="nitan-podcast-2025-W01", pub_date=datetime(2025, 1, 6, tzinfo=timezone.utc),
        )
        channel.append(old_item)
        tree.write(feed, xml_declaration=True, encoding="unicode")

        # Re-run: should keep both
        self._run_generate(tmp_path, monkeypatch)
        tree2 = ET.parse(feed)
        items = tree2.findall(".//item")
        assert len(items) == 2

    def test_newest_first(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        # Seed an old item
        feed = tmp_path / "feed.xml"
        config = _podcast_config()
        rss, channel = _build_channel(config)
        old_item = _build_item(
            title="Old", description="Old", audio_url="https://x.com/old.mp3",
            guid="nitan-podcast-2025-W01", pub_date=datetime(2025, 1, 6, tzinfo=timezone.utc),
        )
        channel.append(old_item)
        ET.indent(rss)
        ET.ElementTree(rss).write(feed, xml_declaration=True, encoding="unicode")

        # Generate current episode
        self._run_generate(tmp_path, monkeypatch)
        tree = ET.parse(feed)
        items = tree.findall(".//item")
        assert len(items) == 2
        # Newest should be first (not the 2025 seed item)
        first_guid = items[0].find("guid").text
        assert not first_guid.startswith("nitan-podcast-2025")
