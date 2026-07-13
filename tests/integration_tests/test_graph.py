import importlib
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from agent import graph as compiled_graph

graph_module = importlib.import_module("agent.graph")

pytestmark = pytest.mark.anyio


def thread_config() -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": f"test-{uuid4()}"}}


async def test_learning_plan_agent_builds_plan_lesson_and_quiz() -> None:
    inputs = {"topic": "LangGraph 智能体"}
    res = await compiled_graph.ainvoke(inputs, thread_config())
    assert res["topic"] == "LangGraph 智能体"
    assert len(res["learning_plan"]) == 3
    assert all(item for item in res["learning_plan"])
    assert len(res["first_lesson"]) > 20
    assert "LangGraph" in res["reference"]
    assert len(res["quiz"]) == 3


async def test_learning_plan_agent_can_skip_quiz() -> None:
    inputs = {
        "topic": "LangGraph 条件边",
        "skip_quiz": True,
        "quiz": ["旧测验题"],
        "reference": "旧资料",
    }
    res = await compiled_graph.ainvoke(inputs, thread_config())
    assert res["topic"] == "LangGraph 条件边"
    assert res["skip_quiz"] is True
    assert len(res["learning_plan"]) == 3
    assert len(res["first_lesson"]) > 20
    assert res["quiz"] == []
    assert res["reference"] == ""


async def test_learning_plan_agent_remembers_progress_in_same_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_learning_plan(topic: str) -> list[str]:
        return [f"{topic} 第一步", f"{topic} 第二步", f"{topic} 第三步"]

    async def fake_generate_lesson(topic: str, learning_goal: str) -> str:
        return f"{topic} 课程：{learning_goal}"

    monkeypatch.setattr(
        graph_module, "generate_learning_plan", fake_generate_learning_plan
    )
    monkeypatch.setattr(graph_module, "generate_lesson", fake_generate_lesson)

    config = thread_config()
    memory_graph = graph_module.build_graph(checkpointer=InMemorySaver())

    first = await memory_graph.ainvoke(
        {"topic": "LangGraph 记忆", "skip_quiz": True},
        config,
    )
    second = await memory_graph.ainvoke(
        {"topic": "继续", "skip_quiz": True},
        config,
    )

    assert first["active_topic"] == "LangGraph 记忆"
    assert first["current_step"] == 1
    assert first["first_lesson"] == "LangGraph 记忆 课程：LangGraph 记忆 第一步"
    assert second["topic"] == "LangGraph 记忆"
    assert second["active_topic"] == "LangGraph 记忆"
    assert second["current_step"] == 2
    assert second["learning_plan"] == first["learning_plan"]
    assert second["first_lesson"] == "LangGraph 记忆 课程：LangGraph 记忆 第二步"
