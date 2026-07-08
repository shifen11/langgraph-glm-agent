"""学习计划 Agent 的最小 LangGraph 示例。

这个版本先不接真实大模型，重点演示 StateGraph 如何用多个节点
逐步更新同一份状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class Context(TypedDict):
    """运行时上下文。

    后续接入真实模型时，可以把模型名、温度、系统提示词等配置放在这里。
    """

    model_name: str


@dataclass
class State:
    """学习计划 Agent 的共享状态。"""

    topic: str = "LangGraph"
    learning_plan: List[str] = field(default_factory=list)
    first_lesson: str = ""
    quiz: List[str] = field(default_factory=list)


async def plan_topic(state: State) -> Dict[str, Any]:
    """根据学习主题生成三步学习计划。"""
    return {
        "learning_plan": [
            f"认识 {state.topic} 的核心概念：state、node、edge。",
            f"用 {state.topic} 写一个多节点工作流。",
            f"给 {state.topic} Agent 增加工具调用、记忆和人工确认。",
        ]
    }


async def explain_topic(state: State) -> Dict[str, Any]:
    """讲解学习计划里的第一个知识点。"""
    first_step = state.learning_plan[0] if state.learning_plan else state.topic
    return {
        "first_lesson": (
            f"第一课：{first_step} "
            "在 LangGraph 里，state 是节点之间传递的数据，"
            "node 是一次处理步骤，edge 决定下一步走向。"
        )
    }


async def make_quiz(state: State) -> Dict[str, Any]:
    """围绕第一课生成小测验。"""
    return {
        "quiz": [
            "State 在 LangGraph 里负责保存什么？",
            "Node 和普通函数有什么关系？",
            "Edge 为什么能表达 Agent 的执行流程？",
        ]
    }


graph = (
    StateGraph(State, context_schema=Context)
    .add_node("plan_topic", plan_topic)
    .add_node("explain_topic", explain_topic)
    .add_node("make_quiz", make_quiz)
    .add_edge(START, "plan_topic")
    .add_edge("plan_topic", "explain_topic")
    .add_edge("explain_topic", "make_quiz")
    .add_edge("make_quiz", END)
    .compile(name="学习计划 Agent")
)
