"""Verify real downloaded-container conversion and failure preservation."""

from pathlib import Path
import shutil
import subprocess

import pytest

from scripts import prepare_audio


pytestmark = pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="Audio integration checks require FFmpeg",
)


@pytest.fixture
def mislabeled_audio(tmp_path: Path) -> Path:
    source = tmp_path / "source.m4a"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i",
         "sine=frequency=440:duration=2", "-c:a", "aac", str(source)],
        check=True, capture_output=True,
    )
    target = tmp_path / "episode.mp3"
    source.rename(target)
    return target


def test_aac_download_becomes_real_mp3_with_measured_duration(mislabeled_audio):
    assert not prepare_audio.is_mp3(prepare_audio.probe(mislabeled_audio))
    assert prepare_audio.prepare(mislabeled_audio) == "00:00:02"
    assert prepare_audio.is_mp3(prepare_audio.probe(mislabeled_audio))


def test_valid_mp3_is_not_reencoded(mislabeled_audio):
    prepare_audio.prepare(mislabeled_audio)
    before = mislabeled_audio.read_bytes()
    assert prepare_audio.prepare(mislabeled_audio) == "00:00:02"
    assert mislabeled_audio.read_bytes() == before


def test_failed_conversion_preserves_download_and_removes_temp(mislabeled_audio, monkeypatch):
    before = mislabeled_audio.read_bytes()
    run = subprocess.run

    def fail_conversion(command, **kwargs):
        if command[0] == "ffmpeg":
            raise subprocess.CalledProcessError(1, command)
        return run(command, **kwargs)

    monkeypatch.setattr(prepare_audio.subprocess, "run", fail_conversion)
    with pytest.raises(subprocess.CalledProcessError):
        prepare_audio.prepare(mislabeled_audio)
    assert mislabeled_audio.read_bytes() == before
    assert list(mislabeled_audio.parent.iterdir()) == [mislabeled_audio]


def test_corrupt_download_is_rejected(tmp_path):
    path = tmp_path / "bad.mp3"
    path.write_text("not audio")
    with pytest.raises(subprocess.CalledProcessError):
        prepare_audio.prepare(path)
    assert path.read_text() == "not audio"
