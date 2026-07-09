from langgraph.pregel import Pregel

from agent.graph import State, graph, route_after_lesson


def test_placeholder() -> None:
    assert isinstance(graph, Pregel)


def test_route_after_lesson_can_skip_quiz() -> None:
    assert route_after_lesson(State(skip_quiz=True)) == "__end__"


def test_route_after_lesson_continues_to_quiz_by_default() -> None:
    assert route_after_lesson(State(skip_quiz=False)) == "collect_reference"
