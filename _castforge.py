"""Helpers to import the sibling CastForge repo during the split transition."""

from __future__ import annotations

import sys
from pathlib import Path


def ensure_castforge_on_path() -> None:
    """Allow local development with a sibling ``castforge`` checkout."""
    try:
        import importlib.util

        if importlib.util.find_spec("castforge.pipeline") is not None:
            return
    except ModuleNotFoundError:
        pass

    root = Path(__file__).resolve().parent
    # A leftover ``castforge/src`` tree (empty or egg-info only) creates a namespace
    # ``castforge`` package that shadows the real package and breaks submodules.
    for repo_candidate in (root.parent / "castforge", root / "castforge"):
        src_dir = repo_candidate / "src"
        if src_dir.is_dir():
            bad = src_dir.resolve()
            sys.path[:] = [p for p in sys.path if Path(p).resolve() != bad]
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
