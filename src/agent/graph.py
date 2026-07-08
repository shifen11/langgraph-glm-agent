"""学习计划 Agent 的 LangGraph 图定义."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from agent.llm import generate_learning_plan, generate_lesson, generate_quiz


@dataclass
class State:
    """学习计划 Agent 的共享状态."""

    topic: str = "LangGraph"
    learning_plan: List[str] = field(default_factory=list)
    first_lesson: str = ""
    quiz: List[str] = field(default_factory=list)


async def plan_topic(state: State) -> Dict[str, Any]:
    """调用 GLM 根据学习主题生成三步学习计划."""
    return {"learning_plan": await generate_learning_plan(state.topic)}


async def explain_topic(state: State) -> Dict[str, Any]:
    """调用 GLM 讲解学习计划里的第一个知识点."""
    first_step = state.learning_plan[0] if state.learning_plan else state.topic
    lesson = await generate_lesson(topic=state.topic, learning_goal=first_step)
    return {"first_lesson": lesson}


async def make_quiz(state: State) -> Dict[str, Any]:
    """调用 GLM 围绕第一课生成小测验."""
    return {"quiz": await generate_quiz(state.topic, state.first_lesson)}


graph = (
    StateGraph(State)
    .add_node("plan_topic", plan_topic)
    .add_node("explain_topic", explain_topic)
    .add_node("make_quiz", make_quiz)
    .add_edge(START, "plan_topic")
    .add_edge("plan_topic", "explain_topic")
    .add_edge("explain_topic", "make_quiz")
    .add_edge("make_quiz", END)
    .compile(name="学习计划 Agent")
)
