import importlib
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

graph_module = importlib.import_module("agent.graph")

pytestmark = pytest.mark.anyio


def thread_config() -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": f"test-{uuid4()}"}}


def memory_graph():
    return graph_module.build_graph(checkpointer=InMemorySaver())


async def approve_plan_and_finish(
    graph,
    inputs: dict[str, object],
    config: dict[str, dict[str, str]],
) -> dict[str, object]:
    interrupted = await graph.ainvoke(inputs, config)
    assert "__interrupt__" in interrupted
    return await graph.ainvoke(Command(resume=True), config)


async def test_learning_plan_agent_builds_plan_lesson_and_quiz() -> None:
    inputs = {"topic": "LangGraph 智能体"}
    res = await approve_plan_and_finish(memory_graph(), inputs, thread_config())
    assert res["topic"] == "LangGraph 智能体"
    assert res["plan_approved"] is True
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
    res = await approve_plan_and_finish(memory_graph(), inputs, thread_config())
    assert res["topic"] == "LangGraph 条件边"
    assert res["skip_quiz"] is True
    assert res["plan_approved"] is True
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
    graph = memory_graph()

    first_interrupted = await graph.ainvoke(
        {"topic": "LangGraph 记忆", "skip_quiz": True},
        config,
    )
    assert "__interrupt__" in first_interrupted
    first = await graph.ainvoke(Command(resume=True), config)
    second = await graph.ainvoke(
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


async def test_learning_plan_agent_can_edit_plan_during_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_generate_learning_plan(topic: str) -> list[str]:
        return [f"{topic} 原计划 1", f"{topic} 原计划 2", f"{topic} 原计划 3"]

    async def fake_generate_lesson(topic: str, learning_goal: str) -> str:
        return f"{topic} 课程：{learning_goal}"

    monkeypatch.setattr(
        graph_module, "generate_learning_plan", fake_generate_learning_plan
    )
    monkeypatch.setattr(graph_module, "generate_lesson", fake_generate_lesson)

    graph = memory_graph()
    config = thread_config()
    interrupted = await graph.ainvoke(
        {"topic": "LangGraph 人工确认", "skip_quiz": True},
        config,
    )
    assert "__interrupt__" in interrupted

    edited_plan = ["先理解 interrupt", "再学习 Command", "最后接入 Studio"]
    res = await graph.ainvoke(
        Command(resume={"approved": True, "learning_plan": edited_plan}),
        config,
    )

    assert res["plan_approved"] is True
    assert res["learning_plan"] == edited_plan
    assert res["first_lesson"] == "LangGraph 人工确认 课程：先理解 interrupt"
