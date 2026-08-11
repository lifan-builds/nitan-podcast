"""Tests for public URLs and identifiers that must remain migration-safe."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlparse

from publisher import episode_guid
from public_contract import (
    PUBLIC_AUDIO_BASE_URL,
    PUBLIC_COVER_ART_URL,
    PUBLIC_FEED_URL,
    PUBLIC_SITE_URL,
    SERIES_GUID_PREFIX,
    week_episode_filename,
    week_episode_url,
)
from rss_feed import _podcast_config


class TestPublicContract:

    def test_public_site_url_is_stable(self):
        assert PUBLIC_SITE_URL == "https://lifan-builds.github.io/nitan-podcast/"

    def test_public_feed_url_is_stable(self):
        assert PUBLIC_FEED_URL == "https://lifan-builds.github.io/nitan-podcast/feed.xml"

    def test_episode_filename_pattern_is_stable(self):
        assert week_episode_filename(2026, 13) == "weekly_meika_2026-W13.mp3"

    def test_episode_url_pattern_is_stable(self):
        assert week_episode_url(2026, 13) == (
            "https://lifan-builds.github.io/nitan-podcast/episodes/weekly_meika_2026-W13.mp3"
        )

    def test_guid_prefix_is_stable(self):
        assert SERIES_GUID_PREFIX == "nitan-podcast"
        assert episode_guid("2026年第13周") == "nitan-podcast-2026-W13"

    def test_rss_defaults_follow_public_contract(self, monkeypatch):
        monkeypatch.delenv("PODCAST_LINK", raising=False)
        monkeypatch.delenv("PODCAST_FEED_URL", raising=False)
        monkeypatch.delenv("PODCAST_COVER_ART_URL", raising=False)
        cfg = _podcast_config()
        assert cfg["link"] == PUBLIC_SITE_URL
        assert cfg["feed_url"] == PUBLIC_FEED_URL
        assert cfg["cover_art_url"] == PUBLIC_COVER_ART_URL

    def test_audio_base_url_is_stable(self):
        assert PUBLIC_AUDIO_BASE_URL == "https://lifan-builds.github.io/nitan-podcast/episodes"

    def test_feed_pages_audio_matches_committed_files(self):
        root = Path(__file__).resolve().parents[1]
        feed = ET.parse(root / "docs" / "feed.xml").getroot()
        enclosures = {
            item.find("enclosure").get("url"): int(item.find("enclosure").get("length", "0"))
            for item in feed.findall("./channel/item")
        }
        weekly_files = sorted((root / "docs" / "episodes").glob("weekly_meika_*.mp3"))
        assert weekly_files
        for audio in weekly_files:
            url = f"{PUBLIC_AUDIO_BASE_URL}/{audio.name}"
            assert url in enclosures, f"{audio.name} is published but missing from RSS"
            assert enclosures[url] == audio.stat().st_size

        for url, length in enclosures.items():
            if not url.startswith(f"{PUBLIC_AUDIO_BASE_URL}/"):
                continue
            name = Path(unquote(urlparse(url).path)).name
            audio = root / "docs" / "episodes" / name
            assert audio.is_file(), f"RSS points to missing Pages audio: {name}"
            assert length == audio.stat().st_size
