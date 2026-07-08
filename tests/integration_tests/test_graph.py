import pytest

from agent import graph

pytestmark = pytest.mark.anyio


async def test_learning_plan_agent_builds_plan_lesson_and_quiz() -> None:
    inputs = {"topic": "LangGraph 智能体"}
    res = await graph.ainvoke(inputs)
    assert res["topic"] == "LangGraph 智能体"
    assert len(res["learning_plan"]) == 3
    assert all(item for item in res["learning_plan"])
    assert len(res["first_lesson"]) > 20
    assert len(res["quiz"]) == 3
