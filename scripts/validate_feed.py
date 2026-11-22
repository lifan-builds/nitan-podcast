#!/usr/bin/env python3
"""Validate the podcast RSS feed: XML structure, audio URL, content-type, file size.

Can check a local file or the live GitHub Pages feed.

Usage:
    python scripts/validate_feed.py                          # live feed
    python scripts/validate_feed.py docs/feed.xml            # local file
    python scripts/validate_feed.py --wait-for-deploy 120    # wait up to 120s for Pages deploy
    python scripts/validate_feed.py --wait-for-deploy 120 --expected-audio-url URL
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from castforge.rss import ITUNES_NS
from public_contract import PUBLIC_FEED_URL

LIVE_FEED_URL = PUBLIC_FEED_URL

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


def validate_item(item: ET.Element, check_live: bool = True, required_live_url: str = "") -> None:
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
        live_required = not required_live_url or url == required_live_url

        def live_issue(msg: str) -> None:
            if live_required:
                fail(msg)
            else:
                warn(msg)

        try:
            hdrs = _curl_head(url)
            status = int(hdrs.get("_status", "0"))
            if status != 200:
                live_issue(f"HTTP {status} (expected 200)")
                return
            ct = hdrs.get("content-type", "")
            cl = hdrs.get("content-length", "0")
            if "audio/mpeg" not in ct and "audio/" not in ct:
                live_issue(f"Server content-type = '{ct}' (expected audio/mpeg)")
            else:
                ok(f"Server content-type = {ct}")
            if cl and int(cl) > 0:
                ok(f"Server content-length = {int(cl):,}")
                if size > 0 and abs(int(cl) - size) > 1024:
                    warn(f"Feed length ({size:,}) != server ({int(cl):,})")
            else:
                warn(f"Server content-length = {cl}")
        except Exception as e:
            live_issue(f"Cannot reach audio URL: {e}")


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


def _newest_enclosure(root: ET.Element) -> ET.Element | None:
    channel = root.find("channel")
    if channel is None:
        return None
    item = channel.find("item")
    return item.find("enclosure") if item is not None else None


def _newest_audio_url(root: ET.Element) -> str:
    enc = _newest_enclosure(root)
    return enc.get("url", "") if enc is not None else ""


def _newest_enclosure_length(root: ET.Element) -> int:
    enc = _newest_enclosure(root)
    if enc is None:
        return 0
    try:
        return int(enc.get("length", "0"))
    except ValueError:
        return 0


def _has_audio_url(items: list[ET.Element], expected_audio_url: str) -> bool:
    for item in items:
        enc = item.find("enclosure")
        if enc is not None and enc.get("url", "") == expected_audio_url:
            return True
    return False


def _poll_until(timeout: int, label: str, check):
    print(f"\nWaiting up to {timeout}s for {label}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = check()
            if result:
                print(f"  {label.capitalize()} detected after {int(time.time() - start)}s")
                return result
        except (OSError, subprocess.SubprocessError, ValueError, ET.ParseError) as exc:
            print(f"  Poll retry ({label}): {exc}")
        time.sleep(10)
    print(f"  Timed out after {timeout}s")
    return None


def wait_for_deploy(expected_url: str, timeout: int) -> bool:
    """Poll until the audio URL returns 200, or timeout."""
    return bool(
        _poll_until(
            timeout,
            "GitHub Pages deploy",
            lambda: int(_curl_head(expected_url).get("_status", "0")) == 200,
        )
    )


def wait_for_feed_deploy(source: str, timeout: int, expected_audio_url: str = "") -> ET.Element | None:
    """Poll live RSS until the newest enclosure is deployed and populated."""
    def _check() -> ET.Element | None:
        root = load_feed(source)
        audio_url = _newest_audio_url(root)
        url_matches = not expected_audio_url or audio_url == expected_audio_url
        return root if url_matches and audio_url and _newest_enclosure_length(root) > 0 else None

    return _poll_until(timeout, "feed deploy", _check)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("source", nargs="?", default=LIVE_FEED_URL)
    parser.add_argument("--wait-for-deploy", type=int, nargs="?", const=120, default=0)
    parser.add_argument("--expected-audio-url", default="")
    parser.add_argument("--local-only", action="store_true")
    parsed = parser.parse_args(argv if argv is not None else sys.argv[1:])

    source = parsed.source
    check_live = not parsed.local_only and not Path(source).is_file()
    deploy_wait = parsed.wait_for_deploy
    expected_audio_url = parsed.expected_audio_url

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

    if deploy_wait and source == LIVE_FEED_URL:
        deployed_root = wait_for_feed_deploy(source, deploy_wait, expected_audio_url)
        if deployed_root is not None:
            root = deployed_root
            channel = root.find("channel")
            items = channel.findall("item") if channel is not None else []
        else:
            warn("Feed deploy not detected; validating the latest fetched feed")

    if expected_audio_url and not _has_audio_url(items, expected_audio_url):
        fail(f"Expected audio URL not found in feed: {expected_audio_url}")

    # If waiting for deploy, check the newest episode URL before item validation.
    if deploy_wait and items:
        audio_url = expected_audio_url or _newest_audio_url(root)
        if audio_url and not wait_for_deploy(audio_url, deploy_wait):
            fail(f"Audio deploy not detected: {audio_url}")

    for item in items:
        validate_item(item, check_live=check_live, required_live_url=expected_audio_url)

    print(f"\n{'=' * 40}")
    print(f"RESULT: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
