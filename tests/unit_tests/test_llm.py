from agent.llm import parse_learning_plan


def test_parse_learning_plan_keeps_three_nonempty_items() -> None:
    text = """
    1. 认识 LangGraph 的 StateGraph
    2. 编写一个多节点工作流
    3. 调试并观察节点输出
    """

    assert parse_learning_plan(text) == [
        "认识 LangGraph 的 StateGraph",
        "编写一个多节点工作流",
        "调试并观察节点输出",
    ]
