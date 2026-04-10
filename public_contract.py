"""Public podcast URLs and identifiers that must remain stable across migrations."""

from __future__ import annotations

SERIES_SLUG = "nitan-podcast"
SERIES_GUID_PREFIX = "nitan-podcast"
EPISODE_FILE_PREFIX = "weekly_meika"

PUBLIC_SITE_URL = "https://lifan-builds.github.io/nitan-podcast/"
PUBLIC_FEED_URL = f"{PUBLIC_SITE_URL}feed.xml"
PUBLIC_AUDIO_BASE_URL = f"{PUBLIC_SITE_URL}episodes"
PUBLIC_COVER_ART_URL = "https://github.com/lifan-builds/nitan-podcast/raw/main/assets/cover.png"


def week_episode_stem(year: int, week: int) -> str:
    """Return the public episode stem, e.g. ``weekly_meika_2026-W13``."""
    return f"{EPISODE_FILE_PREFIX}_{year}-W{week:02d}"


def week_episode_filename(year: int, week: int) -> str:
    """Return the public MP3 filename for an ISO week."""
    return f"{week_episode_stem(year, week)}.mp3"


def week_episode_url(year: int, week: int) -> str:
    """Return the stable GitHub Pages URL for an ISO week episode."""
    return f"{PUBLIC_AUDIO_BASE_URL}/{week_episode_filename(year, week)}"
