"""
SoundCloud track upload via OAuth 2.1 (PKCE).

One-time setup:
  1. Register an app at https://soundcloud.com/you/apps
  2. Set SOUNDCLOUD_CLIENT_ID and SOUNDCLOUD_CLIENT_SECRET in .env
  3. Run: python soundcloud_upload.py login
  4. Pipeline uses --publish-soundcloud to upload + get embed URL

Requires: requests (already in stdlib deps via other modules).
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import logging
import os
import secrets
import sys
import threading
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

logger = logging.getLogger(__name__)

_TOKEN_PATH = Path("~/.nitan-podcast/soundcloud_tokens.json").expanduser()
_REDIRECT_PORT = 18923
_REDIRECT_URI = f"http://localhost:{_REDIRECT_PORT}/callback"
_AUTH_URL = "https://secure.soundcloud.com/authorize"
_TOKEN_URL = "https://secure.soundcloud.com/oauth/token"
_API_BASE = "https://api.soundcloud.com"


# ---------------------------------------------------------------------------
# Token storage
# ---------------------------------------------------------------------------

def _save_tokens(data: dict) -> None:
    _TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    _TOKEN_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Saved SoundCloud tokens to %s", _TOKEN_PATH)


def _load_tokens() -> dict:
    if not _TOKEN_PATH.is_file():
        raise RuntimeError(
            f"No SoundCloud tokens found at {_TOKEN_PATH}. "
            "Run: python soundcloud_upload.py login"
        )
    return json.loads(_TOKEN_PATH.read_text(encoding="utf-8"))


def _get_client_credentials() -> tuple[str, str]:
    cid = os.environ.get("SOUNDCLOUD_CLIENT_ID", "").strip()
    secret = os.environ.get("SOUNDCLOUD_CLIENT_SECRET", "").strip()
    if not cid:
        raise RuntimeError(
            "SOUNDCLOUD_CLIENT_ID not set. "
            "Register an app at https://soundcloud.com/you/apps"
        )
    if not secret:
        raise RuntimeError("SOUNDCLOUD_CLIENT_SECRET not set.")
    return cid, secret


# ---------------------------------------------------------------------------
# OAuth 2.1 PKCE flow
# ---------------------------------------------------------------------------

def _generate_pkce() -> tuple[str, str]:
    """Generate code_verifier and code_challenge for PKCE."""
    verifier = secrets.token_urlsafe(64)[:128]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def login() -> dict:
    """Interactive OAuth login — opens browser, captures callback."""
    from dotenv import load_dotenv
    load_dotenv(override=False)

    client_id, client_secret = _get_client_credentials()
    verifier, challenge = _generate_pkce()
    state = secrets.token_urlsafe(32)

    auth_code: list[str] = []

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            qs = parse_qs(urlparse(self.path).query)
            if "code" in qs:
                auth_code.append(qs["code"][0])
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h2>Nitan Podcast: SoundCloud auth OK!</h2>"
                    b"<p>You can close this tab.</p></body></html>"
                )
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code parameter")

        def log_message(self, format, *args):
            pass  # suppress HTTP logs

    server = http.server.HTTPServer(("127.0.0.1", _REDIRECT_PORT), CallbackHandler)
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    params = {
        "client_id": client_id,
        "redirect_uri": _REDIRECT_URI,
        "response_type": "code",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    url = f"{_AUTH_URL}?{urlencode(params)}"
    print(f"Opening browser for SoundCloud login...\n{url}")
    webbrowser.open(url)

    print("Waiting for callback...")
    thread.join(timeout=120)
    server.server_close()

    if not auth_code:
        raise RuntimeError("No authorization code received. Try again.")

    # Exchange code for tokens
    resp = requests.post(_TOKEN_URL, data={
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": _REDIRECT_URI,
        "code": auth_code[0],
        "code_verifier": verifier,
    })
    resp.raise_for_status()
    tokens = resp.json()
    _save_tokens(tokens)
    print(f"Login successful! Tokens saved to {_TOKEN_PATH}")
    return tokens


def _refresh_access_token() -> dict:
    """Refresh the access token using the stored refresh_token."""
    tokens = _load_tokens()
    rt = tokens.get("refresh_token")
    if not rt:
        raise RuntimeError("No refresh_token. Run: python soundcloud_upload.py login")

    client_id, client_secret = _get_client_credentials()
    resp = requests.post(_TOKEN_URL, data={
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": rt,
    })
    if resp.status_code == 401:
        raise RuntimeError("Refresh token expired. Run: python soundcloud_upload.py login")
    resp.raise_for_status()
    new_tokens = resp.json()
    _save_tokens(new_tokens)
    return new_tokens


def _get_access_token() -> str:
    """Get a valid access token, refreshing if needed."""
    tokens = _load_tokens()
    return tokens["access_token"]


# ---------------------------------------------------------------------------
# Track upload
# ---------------------------------------------------------------------------

def upload_track(
    mp3_path: Path,
    title: str,
    *,
    description: str = "",
    tags: str = "美卡论坛,nitan-podcast,泥潭播客",
    sharing: str = "public",
) -> dict:
    """Upload an MP3 to SoundCloud. Returns the track metadata dict including permalink_url."""
    mp3 = Path(mp3_path).resolve()
    if not mp3.is_file():
        raise FileNotFoundError(f"MP3 not found: {mp3}")

    access_token = _get_access_token()

    def _do_upload(token: str) -> requests.Response:
        with open(mp3, "rb") as f:
            return requests.post(
                f"{_API_BASE}/tracks",
                headers={"Authorization": f"OAuth {token}"},
                data={
                    "track[title]": title,
                    "track[description]": description,
                    "track[tag_list]": tags,
                    "track[sharing]": sharing,
                },
                files={"track[asset_data]": (mp3.name, f, "audio/mpeg")},
                timeout=300,
            )

    resp = _do_upload(access_token)

    # If 401, try refreshing token once
    if resp.status_code == 401:
        logger.info("Access token expired, refreshing...")
        new_tokens = _refresh_access_token()
        resp = _do_upload(new_tokens["access_token"])

    resp.raise_for_status()
    track = resp.json()
    logger.info(
        "Uploaded to SoundCloud: %s (%s)",
        track.get("permalink_url"),
        track.get("id"),
    )
    return track


def upload_episode(
    mp3_path: Path,
    week_label: str,
    *,
    description: str = "",
) -> str:
    """Upload a weekly episode and return the SoundCloud track URL (for Discourse embed)."""
    title = f"泥潭播客 · {week_label}"
    track = upload_track(mp3_path, title, description=description)
    url = track.get("permalink_url", "")
    if not url:
        raise RuntimeError(f"Upload succeeded but no permalink_url in response: {track}")
    return url


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python soundcloud_upload.py login              # One-time OAuth login")
        print("  python soundcloud_upload.py upload <mp3> <title>  # Upload a track")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "login":
        login()
    elif cmd == "upload":
        if len(sys.argv) < 4:
            print("Usage: python soundcloud_upload.py upload <mp3_path> <title>")
            sys.exit(1)
        from dotenv import load_dotenv
        load_dotenv(override=False)
        track = upload_track(Path(sys.argv[2]), sys.argv[3])
        print(track.get("permalink_url", ""))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
