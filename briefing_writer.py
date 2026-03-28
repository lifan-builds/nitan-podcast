"""
Optional Gemini step: turn raw MCP extraction into clean **source text** for
NotebookLM (factual Chinese Markdown — headings, bullets, jargon preserved).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是美卡论坛（USCardForum）的内容编辑。下面是从论坛抓取的本周热门帖与评论要点。

请整理成一份**结构化中文 Markdown**，供播客制作工具作为「来源文档」使用。要求：
- 只输出事实性摘要与要点，不要写双人对话脚本，不要分配主持人台词。
- 保留论坛常用术语与梗（如 5/24、杀全家、史高、冥币）的原样表述。
- 每个主题用小标题；下面用短段落或列表说明背景、争议点、实用结论（若有）。
- 语气客观、信息密度高，便于后续工具基于该文档生成口播内容。

直接输出 Markdown 正文，不要外层代码块标记。"""


def write_briefing_markdown(raw_extraction_text: str) -> str:
    """Call Gemini with UTF-8; return a single Markdown document for NotebookLM upload."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required when briefing is enabled")

    from google import genai

    model_id = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip()
    client = genai.Client(api_key=api_key)

    user_part = f"以下是需要整理的原始素材（可为结构化列表或长文本）：\n\n{raw_extraction_text}"
    logger.info("Calling Gemini model=%r for briefing", model_id)
    response = client.models.generate_content(
        model=model_id,
        contents=[SYSTEM_PROMPT, user_part],
        config=genai.types.GenerateContentConfig(temperature=0.35),
    )

    text = response.text or ""
    if not text.strip():
        raise RuntimeError("Gemini returned empty briefing text")
    return text.strip()
