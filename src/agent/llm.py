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
from openai.types.chat import ChatCompletionMessageParam

LANGGRAPH_DOMAIN_HINT = (
    "这里的 LangGraph 特指 LangChain 生态中用于构建有状态智能体工作流的 "
    "LangGraph 框架，不是自然语言图结构。"
)


def load_local_env() -> None:
    """加载项目根目录的 .env 文件."""
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")


def parse_learning_plan(text: str) -> list[str]:
    """把模型输出解析成最多三条学习计划."""
    return parse_numbered_items(text, limit=3)


def parse_numbered_items(text: str, limit: int) -> list[str]:
    """把模型输出解析成指定数量的条目."""
    items: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+[.)、]\s*", "", line)
        if line:
            items.append(line)
        if len(items) == limit:
            break
    return items


def get_zhipu_client_config() -> tuple[str, str, str]:
    """读取智谱 GLM 客户端配置."""
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
    return api_key, endpoint, model


def build_lesson_messages(
    topic: str, learning_goal: str
) -> list[ChatCompletionMessageParam]:
    """构造第一课讲解提示词."""
    return [
        {
            "role": "system",
            "content": (
                f"你是一个智能体学习教练。{LANGGRAPH_DOMAIN_HINT}"
                "请用中文讲解一个知识点，"
                "面向刚开始学习 LangGraph 和 Agent 的开发者。"
                "要求：先给核心结论，再给一个小例子，最后给一个检查理解的问题。"
            ),
        },
        {
            "role": "user",
            "content": f"学习主题：{topic}\n本课目标：{learning_goal}",
        },
    ]


def build_quiz_messages(
    topic: str, first_lesson: str
) -> list[ChatCompletionMessageParam]:
    """构造测验题提示词."""
    return [
        {
            "role": "system",
            "content": (
                f"你是一个智能体学习教练。{LANGGRAPH_DOMAIN_HINT}"
                "请基于课程内容生成三道中文测验题。"
                "每道题只输出问题本身，每题一行，不要答案，不要额外解释。"
            ),
        },
        {
            "role": "user",
            "content": f"学习主题：{topic}\n课程内容：{first_lesson}",
        },
    ]


async def generate_learning_plan(topic: str) -> list[str]:
    """调用智谱 GLM 生成三步学习计划."""
    api_key, endpoint, model = get_zhipu_client_config()
    client = AsyncOpenAI(api_key=api_key, base_url=endpoint)
    response = await client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    f"你是一个智能体学习教练。{LANGGRAPH_DOMAIN_HINT}"
                    "请输出正好三条学习计划，"
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


async def generate_lesson(topic: str, learning_goal: str) -> str:
    """调用智谱 GLM 生成第一课讲解."""
    api_key, endpoint, model = get_zhipu_client_config()
    client = AsyncOpenAI(api_key=api_key, base_url=endpoint)
    response = await client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=build_lesson_messages(topic, learning_goal),
    )

    content = response.choices[0].message.content or ""
    lesson = content.strip()
    if not lesson:
        raise RuntimeError("智谱 GLM 没有返回第一课讲解。")
    return lesson


async def generate_quiz(topic: str, first_lesson: str) -> list[str]:
    """调用智谱 GLM 生成三道测验题."""
    api_key, endpoint, model = get_zhipu_client_config()
    client = AsyncOpenAI(api_key=api_key, base_url=endpoint)
    response = await client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=build_quiz_messages(topic, first_lesson),
    )

    content = response.choices[0].message.content or ""
    quiz = parse_numbered_items(content, limit=3)
    if len(quiz) != 3:
        raise RuntimeError("智谱 GLM 没有返回三道可解析的测验题。")
    return quiz
