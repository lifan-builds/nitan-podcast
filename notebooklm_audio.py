"""Compatibility wrapper around the extracted CastForge NotebookLM module."""

from __future__ import annotations

from _castforge import ensure_castforge_on_path

ensure_castforge_on_path()

from castforge.notebooklm_audio import publish_weekly_audio, publish_weekly_audio_async

__all__ = ["publish_weekly_audio", "publish_weekly_audio_async"]
