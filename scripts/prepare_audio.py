"""Normalize downloaded audio to the podcast's public MP3 contract."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,format_name",
         "-show_entries", "stream=codec_name,codec_type", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def is_mp3(info: dict) -> bool:
    streams = info.get("streams", [])
    return (
        info["format"]["format_name"] == "mp3"
        and len(streams) == 1
        and streams[0].get("codec_name") == "mp3"
    )


def prepare(path: Path) -> str:
    info = probe(path)
    if not is_mp3(info):
        # Keep the download intact unless conversion and verification succeed.
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".mp3", delete=False) as tmp:
            converted = Path(tmp.name)
        try:
            subprocess.run(
                ["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path),
                 "-map", "0:a:0", "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(converted)],
                check=True, capture_output=True,
            )
            info = probe(converted)
            if not is_mp3(info):
                raise ValueError("Conversion did not produce MP3 audio")
            duration = float(info["format"]["duration"])
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("Audio duration must be finite and positive")
            os.replace(converted, path)
        finally:
            converted.unlink(missing_ok=True)
    duration = float(info["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Audio duration must be finite and positive")
    seconds = max(1, round(duration))
    return f"{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    args = parser.parse_args()
    print(prepare(args.audio))
