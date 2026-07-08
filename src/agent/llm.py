"""智谱 GLM 调用封装.

这里故意保持很薄的一层：LangGraph 节点只关心“我要一份学习计划”，
API key、endpoint、模型名和返回文本解析都放在这个文件里。
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI


def load_local_env() -> None:
    """加载项目根目录的 .env 文件."""
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")


def parse_learning_plan(text: str) -> list[str]:
    """把模型输出解析成最多三条学习计划."""
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+[.)、]\s*", "", line)
        if line:
            items.append(line)
        if len(items) == 3:
            break
    return items


async def generate_learning_plan(topic: str) -> list[str]:
    """调用智谱 GLM 生成三步学习计划."""
    load_local_env()
    api_key = os.getenv("ZHIPU_API_KEY")
    endpoint = os.getenv("ZHIPU_ENDPOINT")
    model = os.getenv("ZHIPU_MODEL")

    if not api_key:
        raise RuntimeError("缺少 ZHIPU_API_KEY，请先在 .env 中配置智谱 API Key。")
    if not endpoint:
        raise RuntimeError("缺少 ZHIPU_ENDPOINT，请先在 .env 中配置智谱接口地址。")
    if not model:
        raise RuntimeError("缺少 ZHIPU_MODEL，请先在 .env 中配置智谱模型名。")

    client = AsyncOpenAI(api_key=api_key, base_url=endpoint)
    response = await client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一个智能体学习教练。请输出正好三条学习计划，"
                    "每条一行，不要标题，不要额外解释。"
                ),
            },
            {
                "role": "user",
                "content": f"学习主题：{topic}",
            },
        ],
    )

    content = response.choices[0].message.content or ""
    plan = parse_learning_plan(content)
    if not plan:
        raise RuntimeError("智谱 GLM 没有返回可解析的学习计划。")
    return plan
