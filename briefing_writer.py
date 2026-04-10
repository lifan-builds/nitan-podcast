"""Compatibility wrapper around the extracted CastForge briefing module."""

from __future__ import annotations

from _castforge import ensure_castforge_on_path

ensure_castforge_on_path()

from castforge.briefing import SYSTEM_PROMPT, write_briefing_markdown

__all__ = ["SYSTEM_PROMPT", "write_briefing_markdown"]
