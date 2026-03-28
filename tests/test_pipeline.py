"""Unit tests for the nitan-pod pipeline modules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from extractor import (
    ENV_FIXTURE,
    _load_fixture,
    _parse_json_list,
    _parse_tool_arguments,
    threads_to_source_markdown,
    tool_result_to_threads,
)
from notebooklm_export import (
    DEFAULT_MARKDOWN_NAME,
    export_for_notebooklm,
)
from briefing_writer import SYSTEM_PROMPT, write_briefing_markdown

SAMPLE_FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "sample_extraction.json"


# ---------------------------------------------------------------------------
# extractor.py -- threads_to_source_markdown
# ---------------------------------------------------------------------------

class TestThreadsToSourceMarkdown:
    """Tests for threads_to_source_markdown()."""

    SAMPLE_THREADS: list[dict[str, Any]] = [
        {
            "title": "示例：某酒店卡史高讨论",
            "category": "信用卡",
            "url": "https://uscardforum.com/d/example",
            "op_summary": "开卡奖励创新高，讨论是否值得冲。",
            "reply_takeaways": ["注意 5/24", "积分是否冥币看用途"],
        },
        {
            "title": "示例：羊毛线报",
            "category": "羊毛",
            "op_summary": "限时活动叠加技巧。",
            "reply_takeaways": ["已实测", "部分地区 YMMV"],
        },
    ]

    def test_header_present(self):
        md = threads_to_source_markdown(self.SAMPLE_THREADS)
        assert "# 美卡论坛（USCardForum）· 本周热点素材" in md

    def test_notebooklm_instruction_present(self):
        md = threads_to_source_markdown(self.SAMPLE_THREADS)
        assert "NotebookLM" in md
        assert "中文" in md

    def test_section_count(self):
        md = threads_to_source_markdown(self.SAMPLE_THREADS)
        assert "## 线索 1" in md
        assert "## 线索 2" in md
        # No extra section
        assert "## 线索 3" not in md

    def test_key_fields_rendered(self):
        md = threads_to_source_markdown(self.SAMPLE_THREADS)
        assert "**title**" in md
        assert "**category**" in md
        assert "示例：某酒店卡史高讨论" in md

    def test_list_values_json_encoded(self):
        md = threads_to_source_markdown(self.SAMPLE_THREADS)
        # reply_takeaways is a list; should be JSON-encoded
        assert "注意 5/24" in md
        assert "积分是否冥币看用途" in md

    def test_empty_list_returns_header_only(self):
        md = threads_to_source_markdown([])
        assert "# 美卡论坛" in md
        assert "## 线索" not in md

    def test_single_thread(self):
        md = threads_to_source_markdown([{"title": "Solo"}])
        assert "## 线索 1" in md
        assert "**title**" in md
        assert "Solo" in md


# ---------------------------------------------------------------------------
# extractor.py -- fixture loading
# ---------------------------------------------------------------------------

class TestFixtureLoading:
    """Tests for _load_fixture via EXTRACTION_FIXTURE_PATH."""

    def test_load_sample_fixture(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(ENV_FIXTURE, str(SAMPLE_FIXTURE))
        threads = _load_fixture()
        assert threads is not None
        assert len(threads) == 2
        assert threads[0]["title"] == "示例：某酒店卡史高讨论"

    def test_no_env_returns_none(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv(ENV_FIXTURE, raising=False)
        assert _load_fixture() is None

    def test_nonexistent_file_raises(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(ENV_FIXTURE, "/tmp/does_not_exist_12345.json")
        with pytest.raises(FileNotFoundError):
            _load_fixture()

    def test_fixture_dict_with_threads_key(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        data = {"threads": [{"title": "A"}, {"title": "B"}]}
        fp = tmp_path / "wrapped.json"
        fp.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setenv(ENV_FIXTURE, str(fp))
        threads = _load_fixture()
        assert threads is not None
        assert len(threads) == 2

    def test_fixture_single_object(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        data = {"title": "Single"}
        fp = tmp_path / "single.json"
        fp.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setenv(ENV_FIXTURE, str(fp))
        threads = _load_fixture()
        assert threads == [{"title": "Single"}]


# ---------------------------------------------------------------------------
# extractor.py -- tool_result_to_threads
# ---------------------------------------------------------------------------

def _make_call_tool_result(
    *,
    structured: Any = None,
    text_contents: list[str] | None = None,
    is_error: bool = False,
) -> MagicMock:
    """Build a lightweight mock of mcp.types.CallToolResult."""
    result = MagicMock()
    result.isError = is_error
    result.structuredContent = structured

    content_blocks: list[MagicMock] = []
    if text_contents:
        # We need to import TextContent to match isinstance checks
        import mcp.types as mtypes
        for t in text_contents:
            block = mtypes.TextContent(type="text", text=t)
            content_blocks.append(block)
    result.content = content_blocks
    return result


class TestToolResultToThreads:
    """Tests for tool_result_to_threads()."""

    def test_structured_list(self):
        result = _make_call_tool_result(structured=[{"title": "A"}, {"title": "B"}])
        threads = tool_result_to_threads(result)
        assert len(threads) == 2

    def test_structured_dict_threads_key(self):
        result = _make_call_tool_result(structured={"threads": [{"title": "X"}]})
        threads = tool_result_to_threads(result)
        assert threads == [{"title": "X"}]

    def test_structured_dict_data_key(self):
        result = _make_call_tool_result(structured={"data": [{"id": 1}]})
        threads = tool_result_to_threads(result)
        assert threads == [{"id": 1}]

    def test_structured_single_dict(self):
        result = _make_call_tool_result(structured={"title": "solo"})
        threads = tool_result_to_threads(result)
        assert threads == [{"title": "solo"}]

    def test_text_content_json_list(self):
        payload = json.dumps([{"title": "T1"}])
        result = _make_call_tool_result(text_contents=[payload])
        threads = tool_result_to_threads(result)
        assert threads == [{"title": "T1"}]

    def test_text_content_json_dict_with_items(self):
        payload = json.dumps({"items": [{"v": 1}]})
        result = _make_call_tool_result(text_contents=[payload])
        threads = tool_result_to_threads(result)
        assert threads == [{"v": 1}]

    def test_text_content_plain_string(self):
        result = _make_call_tool_result(text_contents=["just some raw text"])
        threads = tool_result_to_threads(result)
        assert len(threads) == 1
        assert threads[0]["raw_text"] == "just some raw text"

    def test_empty_text_returns_empty(self):
        result = _make_call_tool_result(text_contents=[""])
        threads = tool_result_to_threads(result)
        assert threads == []

    def test_error_raises(self):
        result = _make_call_tool_result(is_error=True, text_contents=["boom"])
        with pytest.raises(RuntimeError, match="isError=true"):
            tool_result_to_threads(result)


# ---------------------------------------------------------------------------
# extractor.py -- helper parsers
# ---------------------------------------------------------------------------

class TestParseHelpers:

    def test_parse_json_list_valid(self):
        assert _parse_json_list('["a", "b"]') == ["a", "b"]

    def test_parse_json_list_empty(self):
        assert _parse_json_list("") == []
        assert _parse_json_list(None) == []

    def test_parse_json_list_not_list_raises(self):
        with pytest.raises(ValueError):
            _parse_json_list('{"x": 1}')

    def test_parse_tool_arguments_valid(self):
        assert _parse_tool_arguments('{"a": 1}') == {"a": 1}

    def test_parse_tool_arguments_empty(self):
        assert _parse_tool_arguments("") == {}
        assert _parse_tool_arguments(None) == {}

    def test_parse_tool_arguments_not_dict_raises(self):
        with pytest.raises(ValueError):
            _parse_tool_arguments("[1,2]")


# ---------------------------------------------------------------------------
# notebooklm_export.py
# ---------------------------------------------------------------------------

class TestNotebookLMExport:
    """Tests for export_for_notebooklm()."""

    BODY = "# 测试标题\n\n中文内容 with English."

    def test_writes_utf8_file(self, tmp_path: Path):
        path = export_for_notebooklm(self.BODY, export_dir=tmp_path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert content == self.BODY

    def test_default_filename(self, tmp_path: Path):
        path = export_for_notebooklm(self.BODY, export_dir=tmp_path)
        assert path.name == DEFAULT_MARKDOWN_NAME

    def test_custom_filename(self, tmp_path: Path):
        path = export_for_notebooklm(self.BODY, export_dir=tmp_path, filename="custom.md")
        assert path.name == "custom.md"

    def test_creates_nested_directory(self, tmp_path: Path):
        nested = tmp_path / "a" / "b" / "c"
        path = export_for_notebooklm(self.BODY, export_dir=nested)
        assert path.exists()
        assert nested.is_dir()

    def test_chinese_characters_preserved(self, tmp_path: Path):
        chinese_body = "积分是否冥币看用途\n5/24 杀全家 史高"
        path = export_for_notebooklm(chinese_body, export_dir=tmp_path)
        content = path.read_text(encoding="utf-8")
        assert "积分是否冥币看用途" in content
        assert "杀全家" in content
        assert "史高" in content

    def test_returns_absolute_path(self, tmp_path: Path):
        path = export_for_notebooklm(self.BODY, export_dir=tmp_path)
        assert path.is_absolute()


# ---------------------------------------------------------------------------
# briefing_writer.py
# ---------------------------------------------------------------------------

class TestBriefingWriter:
    """Tests for briefing_writer module."""

    def test_system_prompt_exists_and_is_chinese(self):
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 50
        # Contains Chinese characters
        assert "美卡论坛" in SYSTEM_PROMPT
        assert "Markdown" in SYSTEM_PROMPT

    def test_raises_without_gemini_api_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            write_briefing_markdown("some text")

    def test_raises_with_empty_gemini_api_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("GEMINI_API_KEY", "   ")
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            write_briefing_markdown("some text")


# ---------------------------------------------------------------------------
# run_pipeline.py -- argument parsing
# ---------------------------------------------------------------------------

class TestRunPipelineArgParsing:
    """Tests for CLI argument parsing in run_pipeline.main()."""

    def _parse(self, argv: list[str]) -> Any:
        """Parse arguments without running the pipeline."""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--env-file", type=Path, default=Path(".env"))
        parser.add_argument("--skip-briefing", action="store_true")
        parser.add_argument("--export-dir", type=Path, default=None)
        parser.add_argument("--output-filename", default=None)
        parser.add_argument("--dated", action="store_true")
        parser.add_argument("--log-level", default="INFO")
        parser.add_argument("--list-mcp-tools", action="store_true")
        parser.add_argument("--publish-notebooklm", action="store_true")
        parser.add_argument("--notebooklm-audio-out", type=Path, default=None)
        return parser.parse_args(argv)

    def test_defaults(self):
        args = self._parse([])
        assert args.skip_briefing is False
        assert args.dated is False
        assert args.publish_notebooklm is False
        assert args.export_dir is None

    def test_skip_briefing_flag(self):
        args = self._parse(["--skip-briefing"])
        assert args.skip_briefing is True

    def test_dated_flag(self):
        args = self._parse(["--dated"])
        assert args.dated is True

    def test_publish_notebooklm_flag(self):
        args = self._parse(["--publish-notebooklm"])
        assert args.publish_notebooklm is True

    def test_export_dir_argument(self):
        args = self._parse(["--export-dir", "/tmp/out"])
        assert args.export_dir == Path("/tmp/out")

    def test_combined_flags(self):
        args = self._parse(["--skip-briefing", "--dated", "--publish-notebooklm"])
        assert args.skip_briefing is True
        assert args.dated is True
        assert args.publish_notebooklm is True


# ---------------------------------------------------------------------------
# Integration smoke test
# ---------------------------------------------------------------------------

class TestIntegrationSmokeTest:
    """End-to-end: fixture -> markdown export (no network, --skip-briefing)."""

    def test_fixture_to_export(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        """Load sample fixture, generate markdown, export to tmp_path."""
        monkeypatch.setenv(ENV_FIXTURE, str(SAMPLE_FIXTURE))

        # Step 1: extract via fixture
        threads = _load_fixture()
        assert threads is not None and len(threads) > 0

        # Step 2: convert to source markdown
        md = threads_to_source_markdown(threads)
        assert "# 美卡论坛" in md
        assert "## 线索 1" in md

        # Step 3: export
        path = export_for_notebooklm(md, export_dir=tmp_path, filename="smoke.md")
        assert path.exists()

        content = path.read_text(encoding="utf-8")
        assert "美卡论坛" in content
        assert "示例" in content
        assert "信用卡" in content

    def test_full_pipeline_skip_briefing(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        """Run run_pipeline.main() with --skip-briefing using the sample fixture."""
        monkeypatch.setenv(ENV_FIXTURE, str(SAMPLE_FIXTURE))
        # Prevent dotenv from loading real .env that might have conflicting settings
        monkeypatch.setenv("GEMINI_API_KEY", "")

        from run_pipeline import main

        rc = main([
            "--skip-briefing",
            "--export-dir", str(tmp_path),
            "--output-filename", "integration_test.md",
        ])
        assert rc == 0

        out_file = tmp_path / "integration_test.md"
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "美卡论坛" in content
        assert "线索" in content

    def test_markdown_input_skips_extraction(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        """--markdown-input should reuse an existing file without MCP extraction."""
        monkeypatch.setenv("GEMINI_API_KEY", "")
        # Do NOT set EXTRACTION_FIXTURE_PATH — extraction should be skipped entirely
        monkeypatch.delenv(ENV_FIXTURE, raising=False)
        monkeypatch.delenv("MCP_SERVER_COMMAND", raising=False)

        existing_md = tmp_path / "existing.md"
        existing_md.write_text("# Pre-built markdown\n\nSome content.", encoding="utf-8")

        from run_pipeline import main

        rc = main(["--markdown-input", str(existing_md)])
        assert rc == 0
