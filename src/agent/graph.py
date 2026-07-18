"""学习计划 Agent 的 LangGraph 图定义."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph
from langgraph.pregel import Pregel
from langgraph.types import interrupt

from agent.llm import generate_learning_plan, generate_lesson, generate_quiz
from agent.tools import lookup_langgraph_reference

CONTINUE_TOPICS = {"", "继续", "继续学习", "下一课", "next"}


@dataclass
class State:
    """学习计划 Agent 的共享状态."""

    topic: str = "LangGraph"
    active_topic: str = ""
    current_step: int = 0
    plan_approved: bool = False
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
        "plan_approved": False,
        "learning_plan": await generate_learning_plan(active_topic),
        "reference": "",
        "quiz": [],
    }


def parse_plan_review_response(response: Any) -> tuple[bool, list[str] | None]:
    """解析人工审核学习计划后的恢复输入."""
    if isinstance(response, bool):
        return response, None
    if isinstance(response, dict):
        approved = bool(response.get("approved", False))
        learning_plan = response.get("learning_plan")
        if isinstance(learning_plan, list) and all(
            isinstance(item, str) for item in learning_plan
        ):
            return approved, learning_plan
        return approved, None
    return False, None


def review_plan(state: State) -> Dict[str, Any]:
    """暂停等待用户确认学习计划."""
    if state.plan_approved:
        return {}

    response = interrupt(
        {
            "action": "review_learning_plan",
            "message": "请确认学习计划，确认后我再开始讲第一课。",
            "topic": state.active_topic or state.topic,
            "learning_plan": state.learning_plan,
        }
    )
    approved, edited_plan = parse_plan_review_response(response)
    if not approved:
        return {"plan_approved": False}

    update: Dict[str, Any] = {"plan_approved": True}
    if edited_plan is not None:
        update["learning_plan"] = edited_plan
    return update


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


def route_after_plan_review(state: State) -> str:
    """根据学习计划审核结果决定是否开始讲课."""
    if state.plan_approved:
        return "explain_topic"
    return END


def build_graph(checkpointer: Any = None) -> Pregel:
    """构建学习计划 Agent 图.

    `langgraph dev` 会自动处理 persistence，所以导出的 `graph` 不传自定义
    checkpointer。纯 Python 测试或脚本如果要模拟 thread 记忆，可以显式传入
    `InMemorySaver()`。
    """
    return (
        StateGraph(State)
        .add_node("plan_topic", plan_topic)
        .add_node("review_plan", review_plan)
        .add_node("explain_topic", explain_topic)
        .add_node("collect_reference", collect_reference)
        .add_node("make_quiz", make_quiz)
        .add_edge(START, "plan_topic")
        .add_edge("plan_topic", "review_plan")
        .add_conditional_edges("review_plan", route_after_plan_review)
        .add_conditional_edges("explain_topic", route_after_lesson)
        .add_edge("collect_reference", "make_quiz")
        .add_edge("make_quiz", END)
        .compile(name="学习计划 Agent", checkpointer=checkpointer)
    )


graph = build_graph()
