"""
Podcast RSS 2.0 feed generator with iTunes namespace tags.

Produces a feed compatible with Apple Podcasts, Spotify, 小宇宙, and other
podcast directories. Each pipeline run upserts the current episode into the
existing feed file (``docs/feed.xml`` by default).
"""

from __future__ import annotations

import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from publisher import (
    PODCAST_CATEGORY,
    PODCAST_DESCRIPTION,
    PODCAST_LANGUAGE,
    PODCAST_LINK,
    SERIES_NAME,
    SERIES_ZH,
    TAGLINE,
    episode_guid,
    episode_metadata,
)

logger = logging.getLogger(__name__)

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"

DEFAULT_FEED_PATH = Path("docs/feed.xml")

ET.register_namespace("itunes", ITUNES_NS)
ET.register_namespace("atom", ATOM_NS)


# ---------------------------------------------------------------------------
# Config from env
# ---------------------------------------------------------------------------

def _podcast_config() -> dict[str, str]:
    """Read podcast metadata from env vars with sensible defaults."""
    return {
        "title": SERIES_NAME,
        "description": os.environ.get("PODCAST_DESCRIPTION", "").strip() or PODCAST_DESCRIPTION,
        "link": os.environ.get("PODCAST_LINK", "").strip() or PODCAST_LINK,
        "language": PODCAST_LANGUAGE,
        "author": os.environ.get("PODCAST_AUTHOR", "").strip() or SERIES_NAME,
        "owner_name": os.environ.get("PODCAST_OWNER_NAME", "").strip() or SERIES_NAME,
        "owner_email": os.environ.get("PODCAST_OWNER_EMAIL", "").strip() or "lifan.builds@gmail.com",
        "cover_art_url": os.environ.get("PODCAST_COVER_ART_URL", "").strip()
            or "https://github.com/lifan-builds/nitan-podcast/raw/main/assets/cover.png",
        "feed_url": os.environ.get("PODCAST_FEED_URL", "").strip()
            or "https://lifan-builds.github.io/nitan-podcast/feed.xml",
        "category": os.environ.get("PODCAST_CATEGORY", "").strip() or PODCAST_CATEGORY,
    }


# ---------------------------------------------------------------------------
# XML builders
# ---------------------------------------------------------------------------

def _itunes(tag: str) -> str:
    """Return Clark-notation tag for the iTunes namespace."""
    return f"{{{ITUNES_NS}}}{tag}"


def _atom(tag: str) -> str:
    return f"{{{ATOM_NS}}}{tag}"


def _sub(parent: ET.Element, tag: str, text: str | None = None, **attrib: str) -> ET.Element:
    """Add a sub-element with optional text and attributes."""
    el = ET.SubElement(parent, tag, **attrib)
    if text is not None:
        el.text = text
    return el


def _build_channel(config: dict[str, str]) -> tuple[ET.Element, ET.Element]:
    """Build <rss> root and <channel> with iTunes tags. Returns (rss, channel)."""
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    _sub(channel, "title", config["title"])
    _sub(channel, "link", config["link"])
    _sub(channel, "description", config["description"])
    _sub(channel, "language", config["language"])
    _sub(channel, "generator", "nitan-pod RSS generator")

    # Atom self-link (recommended by Apple)
    _sub(channel, _atom("link"), href=config["feed_url"], rel="self", type="application/rss+xml")

    # iTunes channel tags
    _sub(channel, _itunes("author"), config["author"])
    _sub(channel, _itunes("summary"), config["description"])
    _sub(channel, _itunes("type"), "episodic")
    _sub(channel, _itunes("explicit"), "false")
    _sub(channel, _itunes("category"), text=config["category"])

    if config["cover_art_url"]:
        _sub(channel, _itunes("image"), href=config["cover_art_url"])

    owner = _sub(channel, _itunes("owner"))
    _sub(owner, _itunes("name"), config["owner_name"])
    if config["owner_email"]:
        _sub(owner, _itunes("email"), config["owner_email"])

    return rss, channel


def _build_item(
    title: str,
    description: str,
    audio_url: str,
    guid: str,
    pub_date: datetime,
    duration: str = "00:06:00",
    file_size: int = 0,
) -> ET.Element:
    """Build a single <item> element for an episode."""
    item = ET.Element("item")
    _sub(item, "title", title)
    _sub(item, "description", description)
    _sub(item, "pubDate", format_datetime(pub_date, usegmt=True))
    _sub(item, "guid", guid, isPermaLink="false")
    _sub(item, "enclosure", url=audio_url, length=str(file_size), type="audio/mpeg")
    _sub(item, _itunes("duration"), duration)
    _sub(item, _itunes("explicit"), "false")
    return item


# ---------------------------------------------------------------------------
# Feed persistence
# ---------------------------------------------------------------------------

def _load_existing_items(feed_path: Path) -> list[ET.Element]:
    """Parse existing feed.xml and return its <item> elements."""
    if not feed_path.is_file():
        return []
    try:
        tree = ET.parse(feed_path)
        channel = tree.find("channel")
        if channel is None:
            return []
        return list(channel.findall("item"))
    except ET.ParseError:
        logger.warning("Failed to parse existing feed at %s; starting fresh", feed_path)
        return []


def _find_item_guid(item: ET.Element) -> str | None:
    guid_el = item.find("guid")
    return guid_el.text if guid_el is not None else None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def _detect_file_size(audio_url: str, mp3_path: Path | None = None) -> int:
    """Best-effort MP3 file size detection: explicit path > URL-derived local > 0."""
    if mp3_path and Path(mp3_path).is_file():
        return Path(mp3_path).stat().st_size
    url_match = re.search(r"[\w-]+\.mp3", audio_url)
    if url_match:
        local = Path("releases") / url_match.group(0)
        if local.is_file():
            return local.stat().st_size
    return 0


def generate_rss_feed(
    markdown_export_path: Path,
    feed_path: Path | None = None,
    *,
    audio_url: str,
    duration: str = "00:06:00",
    threads: list[dict[str, str]] | None = None,
    file_size: int | None = None,
    mp3_path: Path | None = None,
) -> Path:
    """Generate or update the podcast RSS feed with the current episode.

    Reads episode metadata from the exported Markdown, upserts the episode
    into the feed (matched by GUID), and writes the XML.

    If *threads* is provided, passes them to episode_metadata() directly
    instead of re-parsing the markdown via regex.

    *file_size* overrides auto-detection. *mp3_path* points to the local MP3
    for size detection when the URL filename doesn't match.
    """
    out = (feed_path or DEFAULT_FEED_PATH).resolve()
    md_path = Path(markdown_export_path).resolve()
    md_content = md_path.read_text(encoding="utf-8")

    meta = episode_metadata(md_content, threads=threads)
    guid = episode_guid(meta["week_label"])

    if file_size is None:
        file_size = _detect_file_size(audio_url, mp3_path)
    if file_size == 0:
        logger.warning("MP3 file size is 0 — podcast players may refuse to play this episode")

    pub_date = datetime.now(timezone.utc)

    new_item = _build_item(
        title=meta["title"],
        description=meta["description"],
        audio_url=audio_url,
        guid=guid,
        pub_date=pub_date,
        duration=duration,
        file_size=file_size,
    )

    # Load existing items and upsert
    existing = _load_existing_items(out)
    items = [i for i in existing if _find_item_guid(i) != guid]
    items.insert(0, new_item)  # newest first

    # Build full feed
    config = _podcast_config()
    rss, channel = _build_channel(config)
    for item in items:
        channel.append(item)

    ET.indent(rss, space="  ")
    out.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(rss)
    tree.write(out, xml_declaration=True, encoding="unicode")
    # ElementTree.write() omits trailing newline; append one for POSIX compliance
    out.write_text(out.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")

    logger.info("RSS feed updated: %s (%d episode(s))", out, len(items))
    return out
