"""学习计划 Agent 的 LangGraph 图定义."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph
from langgraph.pregel import Pregel

from agent.llm import generate_learning_plan, generate_lesson, generate_quiz
from agent.tools import lookup_langgraph_reference

CONTINUE_TOPICS = {"", "继续", "继续学习", "下一课", "next"}


@dataclass
class State:
    """学习计划 Agent 的共享状态."""

    topic: str = "LangGraph"
    active_topic: str = ""
    current_step: int = 0
    skip_quiz: bool = False
    learning_plan: List[str] = field(default_factory=list)
    first_lesson: str = ""
    reference: str = ""
    quiz: List[str] = field(default_factory=list)


def is_continue_request(topic: str) -> bool:
    """判断用户是否想沿用当前学习线程继续下一课."""
    return topic.strip().lower() in CONTINUE_TOPICS


async def plan_topic(state: State) -> Dict[str, Any]:
    """调用 GLM 根据学习主题生成三步学习计划."""
    topic = state.topic.strip()
    if is_continue_request(topic) and state.learning_plan:
        active_topic = state.active_topic or "LangGraph"
        return {"topic": active_topic, "active_topic": active_topic}

    if state.learning_plan and state.active_topic == topic:
        return {}

    active_topic = topic or state.active_topic or "LangGraph"
    return {
        "topic": active_topic,
        "active_topic": active_topic,
        "current_step": 0,
        "learning_plan": await generate_learning_plan(active_topic),
        "reference": "",
        "quiz": [],
    }


async def explain_topic(state: State) -> Dict[str, Any]:
    """调用 GLM 讲解学习计划里的第一个知识点."""
    topic = state.active_topic or state.topic
    step_index = min(state.current_step, max(len(state.learning_plan) - 1, 0))
    learning_goal = state.learning_plan[step_index] if state.learning_plan else topic
    next_step = min(state.current_step + 1, max(len(state.learning_plan), 1))
    lesson = await generate_lesson(topic=topic, learning_goal=learning_goal)
    if state.skip_quiz:
        return {
            "first_lesson": lesson,
            "current_step": next_step,
            "reference": "",
            "quiz": [],
        }
    return {"first_lesson": lesson, "current_step": next_step}


async def collect_reference(state: State) -> Dict[str, Any]:
    """调用本地工具查询参考资料."""
    topic = state.active_topic or state.topic
    return {"reference": lookup_langgraph_reference(topic)}


async def make_quiz(state: State) -> Dict[str, Any]:
    """调用 GLM 围绕第一课生成小测验."""
    topic = state.active_topic or state.topic
    return {
        "quiz": await generate_quiz(
            topic=topic,
            first_lesson=state.first_lesson,
            reference=state.reference,
        )
    }


def route_after_lesson(state: State) -> str:
    """根据输入决定讲解后是否进入测验节点."""
    if state.skip_quiz:
        return END
    return "collect_reference"


def build_graph(checkpointer: Any = None) -> Pregel:
    """构建学习计划 Agent 图.

    `langgraph dev` 会自动处理 persistence，所以导出的 `graph` 不传自定义
    checkpointer。纯 Python 测试或脚本如果要模拟 thread 记忆，可以显式传入
    `InMemorySaver()`。
    """
    return (
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
        .compile(name="学习计划 Agent", checkpointer=checkpointer)
    )


graph = build_graph()
