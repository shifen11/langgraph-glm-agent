"""学习计划 Agent 的 LangGraph 图定义."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from agent.llm import generate_learning_plan, generate_lesson, generate_quiz
from agent.tools import lookup_langgraph_reference


@dataclass
class State:
    """学习计划 Agent 的共享状态."""

    topic: str = "LangGraph"
    skip_quiz: bool = False
    learning_plan: List[str] = field(default_factory=list)
    first_lesson: str = ""
    reference: str = ""
    quiz: List[str] = field(default_factory=list)


async def plan_topic(state: State) -> Dict[str, Any]:
    """调用 GLM 根据学习主题生成三步学习计划."""
    return {"learning_plan": await generate_learning_plan(state.topic)}


async def explain_topic(state: State) -> Dict[str, Any]:
    """调用 GLM 讲解学习计划里的第一个知识点."""
    first_step = state.learning_plan[0] if state.learning_plan else state.topic
    lesson = await generate_lesson(topic=state.topic, learning_goal=first_step)
    if state.skip_quiz:
        return {"first_lesson": lesson, "reference": "", "quiz": []}
    return {"first_lesson": lesson}


async def collect_reference(state: State) -> Dict[str, Any]:
    """调用本地工具查询参考资料."""
    return {"reference": lookup_langgraph_reference(state.topic)}


async def make_quiz(state: State) -> Dict[str, Any]:
    """调用 GLM 围绕第一课生成小测验."""
    return {
        "quiz": await generate_quiz(
            topic=state.topic,
            first_lesson=state.first_lesson,
            reference=state.reference,
        )
    }


def route_after_lesson(state: State) -> str:
    """根据输入决定讲解后是否进入测验节点."""
    if state.skip_quiz:
        return END
    return "collect_reference"


graph = (
    StateGraph(State)
    .add_node("plan_topic", plan_topic)
    .add_node("explain_topic", explain_topic)
    .add_node("collect_reference", collect_reference)
    .add_node("make_quiz", make_quiz)
    .add_edge(START, "plan_topic")
    .add_edge("plan_topic", "explain_topic")
    .add_conditional_edges("explain_topic", route_after_lesson)
    .add_edge("collect_reference", "make_quiz")
    .add_edge("make_quiz", END)
    .compile(name="学习计划 Agent")
)
