"""学习 Agent 使用的本地工具."""

from __future__ import annotations


def lookup_langgraph_reference(topic: str) -> str:
    """根据学习主题返回一段本地资料."""
    normalized_topic = topic.lower()
    if "条件" in topic or "conditional" in normalized_topic:
        return (
            "LangGraph 的条件边用于根据当前 State 选择下一步节点。"
            "在 Python 中通常通过 StateGraph.add_conditional_edges(...) 注册路由函数，"
            "路由函数读取 State 后返回下一个节点名或 END。"
        )
    if "工具" in topic or "tool" in normalized_topic:
        return (
            "工具调用是 Agent 获取外部信息或执行动作的方式。"
            "在 LangGraph 中，可以把工具调用做成普通节点：节点读取 State，"
            "调用工具函数，再把工具结果写回 State 供后续节点使用。"
        )
    if "state" in normalized_topic or "状态" in topic:
        return (
            "LangGraph 的 State 是节点之间共享和传递的数据结构。"
            "每个节点返回一个字典，StateGraph 会把这些字段合并回 State，"
            "后续节点可以继续读取更新后的状态。"
        )
    return (
        "LangGraph 是 LangChain 生态中用于构建有状态智能体工作流的框架。"
        "它把工作流拆成节点和边，并通过 State 在节点之间传递上下文。"
    )
