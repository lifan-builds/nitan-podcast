"""
Optional Gemini step: turn raw MCP extraction into engaging **source text** for
NotebookLM (story-driven Chinese Markdown — jargon, community reactions preserved).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是美卡论坛（USCardForum）的资深编辑，正在为一档播客准备素材文档。\
下面是从论坛抓取的本周热门帖与评论要点。

请整理成一份**结构化中文 Markdown**，供播客制作工具作为「来源文档」使用。要求：
- 每个话题写成一个"小故事"——有起因、社区反应、结论或争议点。不要只干巴巴列要点。
- 突出社区互动：有人支持、有人反对、有人分享亲身经历。引用精选回复中的具体观点（如"有网友说……"）。
- 保留论坛常用术语与梗（如 5/24、杀全家、史高、冥币）的原样表述。
- 每个主题用小标题；下面用 2-3 段话讲清楚这个话题为什么火、大家在聊什么、有什么实用结论。
- 标注话题类型：🔥争议、📦干货分享、🐑羊毛线报、📖攻略教程。
- 语气生动但不夸张，像在给朋友讲"你知道这周论坛出了什么事吗？"
- 不要写双人对话脚本，不要分配主持人台词。

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
        config=genai.types.GenerateContentConfig(temperature=0.5),
    )

    text = response.text or ""
    if not text.strip():
        raise RuntimeError("Gemini returned empty briefing text")
    return text.strip()
