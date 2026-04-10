"""Compatibility wrapper around the extracted CastForge export module."""

from __future__ import annotations

from _castforge import ensure_castforge_on_path

ensure_castforge_on_path()

from castforge.export import DEFAULT_EXPORT_DIR, DEFAULT_MARKDOWN_NAME, export_for_notebooklm

__all__ = ["DEFAULT_EXPORT_DIR", "DEFAULT_MARKDOWN_NAME", "export_for_notebooklm"]
