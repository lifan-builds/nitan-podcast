"""Normalize downloaded audio to the podcast's public MP3 contract."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import tempfile


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,format_name",
         "-show_entries", "stream=codec_name,codec_type", "-of", "json", str(path.absolute())],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def is_mp3(info: dict) -> bool:
    match info:
        case {"format": {"format_name": "mp3"},
              "streams": [{"codec_type": "audio", "codec_name": "mp3"}]}:
            return True
    return False


def mp3_duration(info: dict, path: Path) -> float:
    if not is_mp3(info):
        raise ValueError(
            f"{path}: expected format.format_name=mp3 and exactly one stream "
            "with codec_type=audio and codec_name=mp3"
        )
    value = info["format"].get("duration")
    error = f"{path}: format.duration must be finite and positive (got {value!r})"
    try:
        duration = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(error) from None
    if isinstance(value, bool) or not math.isfinite(duration) or duration <= 0:
        raise ValueError(error)
    return duration


def prepare(path: Path) -> str:
    info = probe(path)
    if is_mp3(info):
        duration = mp3_duration(info, path)
    else:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".mp3", delete=False) as tmp:
            converted = Path(tmp.name)
        try:
            subprocess.run(
                ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path.absolute()),
                 "-map", "0:a:0", "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(converted)],
                check=True, capture_output=True,
            )
            duration = mp3_duration(probe(converted), path)
            converted.chmod(stat.S_IMODE(path.stat().st_mode))
            os.replace(converted, path)
        finally:
            converted.unlink(missing_ok=True)
    seconds = max(1, round(duration))
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()
    print(prepare(args.audio))
