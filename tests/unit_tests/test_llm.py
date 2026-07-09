from agent.llm import build_lesson_messages, build_quiz_messages, parse_learning_plan


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


def test_build_lesson_messages_contains_topic_and_goal() -> None:
    messages = build_lesson_messages(
        topic="LangGraph 条件边",
        learning_goal="掌握条件边在 LangGraph 中的定义和作用。",
    )

    assert messages[0]["role"] == "system"
    assert "学习教练" in messages[0]["content"]
    assert "LangChain 生态" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "LangGraph 条件边" in messages[1]["content"]
    assert "掌握条件边" in messages[1]["content"]


def test_build_quiz_messages_contains_topic_lesson_and_count() -> None:
    messages = build_quiz_messages(
        topic="LangGraph 状态传递",
        first_lesson="State 是节点之间传递和更新的数据。",
        reference="StateGraph 会把节点返回的字段合并回 State。",
    )

    assert messages[0]["role"] == "system"
    assert "三道" in messages[0]["content"]
    assert "LangChain 生态" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "LangGraph 状态传递" in messages[1]["content"]
    assert "State 是节点之间传递和更新的数据" in messages[1]["content"]
    assert "StateGraph 会把节点返回的字段合并回 State" in messages[1]["content"]
