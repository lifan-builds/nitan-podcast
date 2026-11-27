"""Verify real downloaded-container conversion and failure preservation."""

from pathlib import Path
import shutil
import stat
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


def test_dash_prefixed_relative_filename(mislabeled_audio, monkeypatch):
    monkeypatch.chdir(mislabeled_audio.parent)
    path = Path("-episode.mp3")
    mislabeled_audio.rename(path)
    assert prepare_audio.prepare(path) == "00:00:02"
    assert prepare_audio.is_mp3(prepare_audio.probe(path))


def test_conversion_preserves_public_read_permissions(mislabeled_audio):
    mislabeled_audio.chmod(0o644)
    prepare_audio.prepare(mislabeled_audio)
    assert stat.S_IMODE(mislabeled_audio.stat().st_mode) == 0o644
    assert prepare_audio.is_mp3(prepare_audio.probe(mislabeled_audio))


@pytest.mark.parametrize("fields", [
    {}, {"duration": None}, {"duration": "N/A"}, {"duration": "0"},
    {"duration": "-1"}, {"duration": "inf"}, {"duration": "nan"},
])
def test_invalid_duration_preserves_download(mislabeled_audio, monkeypatch, fields):
    probe = prepare_audio.probe
    before = mislabeled_audio.read_bytes()

    def probe_with_invalid_duration(path):
        info = probe(path)
        if path != mislabeled_audio:
            info["format"] = {"format_name": "mp3", **fields}
        return info

    monkeypatch.setattr(prepare_audio, "probe", probe_with_invalid_duration)
    with pytest.raises(ValueError, match=r"episode\.mp3: format\.duration must be finite and positive"):
        prepare_audio.prepare(mislabeled_audio)
    assert mislabeled_audio.read_bytes() == before
    assert list(mislabeled_audio.parent.iterdir()) == [mislabeled_audio]


@pytest.mark.parametrize("streams", [
    [], [{"codec_type": "video", "codec_name": "mp3"}],
    [{"codec_type": "audio", "codec_name": "aac"}],
    [{"codec_type": "audio", "codec_name": "mp3"}] * 2,
])
def test_final_mp3_requires_one_mp3_audio_stream(streams):
    info = {"format": {"format_name": "mp3", "duration": "1"}, "streams": streams}
    with pytest.raises(ValueError, match=r"episode\.mp3: .*exactly one stream"):
        prepare_audio.mp3_duration(info, Path("episode.mp3"))
