#!/usr/bin/env python3
"""Validate the podcast RSS feed: XML structure, audio URL, content-type, file size.

Can check a local file or the live GitHub Pages feed.

Usage:
    python scripts/validate_feed.py                          # live feed
    python scripts/validate_feed.py docs/feed.xml            # local file
    python scripts/validate_feed.py --wait-for-deploy 120    # wait up to 120s for Pages deploy
"""

from __future__ import annotations

import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

LIVE_FEED_URL = "https://lifan-builds.github.io/nitan-podcast/feed.xml"
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"

errors: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"  FAIL: {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"  WARN: {msg}")


def ok(msg: str) -> None:
    print(f"  OK:   {msg}")


def validate_channel(channel: ET.Element) -> None:
    """Check required channel-level tags."""
    print("\n[Channel]")
    for tag in ("title", "link", "description", "language"):
        el = channel.find(tag)
        if el is None or not (el.text or "").strip():
            fail(f"Missing or empty <{tag}>")
        else:
            ok(f"<{tag}> = {el.text.strip()[:60]}")


def _curl_head(url: str) -> dict[str, str]:
    """Run curl -sIL and parse response headers. Returns lowercase header dict."""
    result = subprocess.run(
        ["curl", "-sIL", "--max-time", "15", url],
        capture_output=True, text=True,
    )
    headers: dict[str, str] = {}
    status = 0
    for line in result.stdout.splitlines():
        if line.upper().startswith("HTTP/"):
            # Take the last status line (after redirects)
            parts = line.split(None, 2)
            if len(parts) >= 2:
                try:
                    status = int(parts[1])
                except ValueError:
                    pass
        elif ":" in line:
            key, _, val = line.partition(":")
            headers[key.strip().lower()] = val.strip()
    headers["_status"] = str(status)
    return headers


def _curl_fetch(url: str) -> bytes:
    """Fetch URL content via curl."""
    result = subprocess.run(
        ["curl", "-sL", "--max-time", "15", url],
        capture_output=True,
    )
    return result.stdout


def validate_item(item: ET.Element, check_live: bool = True) -> None:
    """Validate a single <item> episode entry."""
    title_el = item.find("title")
    title = (title_el.text or "?") if title_el is not None else "?"
    print(f"\n[Episode: {title}]")

    # Required tags
    for tag in ("title", "description", "pubDate", "guid"):
        el = item.find(tag)
        if el is None or not (el.text or "").strip():
            fail(f"Missing or empty <{tag}>")

    # Enclosure
    enc = item.find("enclosure")
    if enc is None:
        fail("Missing <enclosure>")
        return

    url = enc.get("url", "")
    length = enc.get("length", "0")
    mime = enc.get("type", "")

    if not url:
        fail("Empty enclosure URL")
    else:
        ok(f"URL = {url}")

    if mime != "audio/mpeg":
        fail(f"Enclosure type = '{mime}' (expected 'audio/mpeg')")
    else:
        ok("type = audio/mpeg")

    try:
        size = int(length)
    except ValueError:
        size = -1

    if size <= 0:
        fail(f"Enclosure length = {length} (must be > 0)")
    else:
        ok(f"length = {size:,} bytes")

    # Duration
    dur_el = item.find(f"{{{ITUNES_NS}}}duration")
    if dur_el is not None and dur_el.text:
        ok(f"duration = {dur_el.text}")
    else:
        warn("Missing <itunes:duration>")

    # Live URL check
    if check_live and url:
        print(f"\n[Live check: {url}]")
        try:
            hdrs = _curl_head(url)
            status = int(hdrs.get("_status", "0"))
            if status != 200:
                fail(f"HTTP {status} (expected 200)")
                return
            ct = hdrs.get("content-type", "")
            cl = hdrs.get("content-length", "0")
            if "audio/mpeg" not in ct and "audio/" not in ct:
                fail(f"Server content-type = '{ct}' (expected audio/mpeg)")
            else:
                ok(f"Server content-type = {ct}")
            if cl and int(cl) > 0:
                ok(f"Server content-length = {int(cl):,}")
                if size > 0 and abs(int(cl) - size) > 1024:
                    warn(f"Feed length ({size:,}) != server ({int(cl):,})")
            else:
                warn(f"Server content-length = {cl}")
        except Exception as e:
            fail(f"Cannot reach audio URL: {e}")


def load_feed(source: str) -> ET.Element:
    """Load feed from local path or URL. Returns the root element."""
    path = Path(source)
    if path.is_file():
        print(f"Validating local feed: {path}")
        return ET.parse(path).getroot()

    print(f"Fetching live feed: {source}")
    data = _curl_fetch(source)
    if not data:
        raise RuntimeError(f"Failed to fetch feed from {source}")
    return ET.fromstring(data)


def wait_for_deploy(expected_url: str, timeout: int) -> bool:
    """Poll until the audio URL returns 200, or timeout."""
    print(f"\nWaiting up to {timeout}s for GitHub Pages deploy...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            hdrs = _curl_head(expected_url)
            if int(hdrs.get("_status", "0")) == 200:
                elapsed = int(time.time() - start)
                print(f"  Deploy detected after {elapsed}s")
                return True
        except Exception:
            pass
        time.sleep(10)
    print(f"  Timed out after {timeout}s")
    return False


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]

    source = LIVE_FEED_URL
    check_live = True
    deploy_wait = 0

    i = 0
    while i < len(args):
        if args[i] == "--wait-for-deploy":
            deploy_wait = int(args[i + 1]) if i + 1 < len(args) else 120
            i += 2
        elif args[i] == "--local-only":
            check_live = False
            i += 1
        else:
            source = args[i]
            if Path(source).is_file():
                check_live = False
            i += 1

    root = load_feed(source)
    channel = root.find("channel")
    if channel is None:
        fail("No <channel> in feed")
        print(f"\n{'=' * 40}")
        print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1

    validate_channel(channel)

    items = channel.findall("item")
    if not items:
        fail("No episodes in feed")
    else:
        ok(f"{len(items)} episode(s)")

    # If waiting for deploy, check the newest episode URL first
    if deploy_wait and items:
        enc = items[0].find("enclosure")
        if enc is not None:
            audio_url = enc.get("url", "")
            if audio_url and not wait_for_deploy(audio_url, deploy_wait):
                warn("Deploy not detected; live checks may fail")

    for item in items:
        validate_item(item, check_live=check_live)

    print(f"\n{'=' * 40}")
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
