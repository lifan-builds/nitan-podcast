"""Helpers to import the sibling CastForge repo during the split transition."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_castforge_on_path() -> None:
    """Allow local development with a sibling ``castforge`` checkout."""
    try:
        import castforge  # noqa: F401
        return
    except ImportError:
        pass

    root = Path(__file__).resolve().parent
    candidates = [
        Path(sys.prefix),
        root.parent / "castforge",
        root / "castforge",
    ]
    for candidate in candidates:
        pkg_dir = candidate / "castforge"
        if pkg_dir.is_dir():
            sys.path.insert(0, str(candidate))
            return

    raise ImportError(
        "CastForge is not importable. Install it or clone the sibling repo at ../castforge."
    )
