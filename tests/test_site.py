"""Static-site contract checks for the public GitHub Pages root."""

from pathlib import Path


SITE = (Path(__file__).resolve().parents[1] / "docs" / "index.html").read_text(encoding="utf-8")


def test_site_links_subscription_surfaces() -> None:
    assert "feed.xml" in SITE
    assert "podcasts.apple.com" in SITE
    assert "open.spotify.com" in SITE
    assert "uscardforum.com" in SITE


def test_site_attributes_castforge_and_loads_episode_archive() -> None:
    assert "github.com/lifan-builds/castforge" in SITE
    assert 'fetch("feed.xml")' in SITE
    assert "<audio" not in SITE  # players are created from the canonical feed at runtime
