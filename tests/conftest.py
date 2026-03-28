"""Shared pytest fixtures for nitan-pod tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_FIXTURE = PROJECT_ROOT / "fixtures" / "sample_extraction.json"

SAMPLE_THREADS: list[dict[str, Any]] = [
    {
        "title": "示例：某酒店卡史高讨论",
        "category": "信用卡",
        "url": "https://uscardforum.com/d/example",
        "op_summary": "开卡奖励创新高，讨论是否值得冲。",
        "reply_takeaways": ["注意 5/24", "积分是否冥币看用途"],
        "like_count": "42",
        "views": "1200",
    },
    {
        "title": "示例：羊毛线报",
        "category": "羊毛",
        "url": "https://uscardforum.com/d/example2",
        "op_summary": "限时活动叠加技巧。",
        "reply_takeaways": ["已实测", "部分地区 YMMV"],
        "like_count": "18",
        "views": "500",
    },
]


@pytest.fixture
def sample_threads() -> list[dict[str, Any]]:
    """Two sample thread dicts with all common fields."""
    return [dict(t) for t in SAMPLE_THREADS]


@pytest.fixture
def sample_fixture_path() -> Path:
    return SAMPLE_FIXTURE


@pytest.fixture
def sample_markdown(sample_threads: list[dict[str, Any]]) -> str:
    """Markdown generated from sample_threads via threads_to_source_markdown."""
    from extractor import threads_to_source_markdown
    return threads_to_source_markdown(sample_threads)
