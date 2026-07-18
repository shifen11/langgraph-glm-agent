from langgraph.pregel import Pregel

from agent.graph import (
    State,
    graph,
    parse_plan_review_response,
    route_after_lesson,
    route_after_plan_review,
)


def test_placeholder() -> None:
    assert isinstance(graph, Pregel)


def test_route_after_lesson_can_skip_quiz() -> None:
    assert route_after_lesson(State(skip_quiz=True)) == "__end__"


def test_route_after_lesson_continues_to_quiz_by_default() -> None:
    assert route_after_lesson(State(skip_quiz=False)) == "collect_reference"


def test_route_after_plan_review_continues_after_approval() -> None:
    assert route_after_plan_review(State(plan_approved=True)) == "explain_topic"


def test_route_after_plan_review_ends_without_approval() -> None:
    assert route_after_plan_review(State(plan_approved=False)) == "__end__"


def test_parse_plan_review_response_accepts_bool() -> None:
    assert parse_plan_review_response(True) == (True, None)


def test_parse_plan_review_response_accepts_edited_plan() -> None:
    assert parse_plan_review_response(
        {"approved": True, "learning_plan": ["第一步", "第二步"]}
    ) == (True, ["第一步", "第二步"])
