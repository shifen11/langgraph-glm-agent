from agent.tools import lookup_langgraph_reference


def test_lookup_langgraph_reference_returns_relevant_reference() -> None:
    reference = lookup_langgraph_reference("LangGraph 条件边")

    assert "条件边" in reference
    assert "add_conditional_edges" in reference
