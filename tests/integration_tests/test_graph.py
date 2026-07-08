import pytest

from agent import graph

pytestmark = pytest.mark.anyio


async def test_learning_plan_agent_builds_plan_lesson_and_quiz() -> None:
    inputs = {"topic": "LangGraph 智能体"}
    res = await graph.ainvoke(inputs)
    assert res["topic"] == "LangGraph 智能体"
    assert len(res["learning_plan"]) == 3
    assert "LangGraph 智能体" in res["learning_plan"][0]
    assert "第一课" in res["first_lesson"]
    assert len(res["quiz"]) == 3
