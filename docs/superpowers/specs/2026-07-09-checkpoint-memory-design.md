# Checkpoint 记忆设计

## 目标

把学习计划 Agent 从“每次都从头开始”改成“同一个 thread 里能记住学习进度”。第一阶段只做 LangGraph 的短期记忆，方便学习 `checkpointer`、`thread_id` 和 State 恢复机制。

## 范围

- 使用 `langgraph.checkpoint.memory.InMemorySaver`。
- 在 `State` 中增加 `active_topic` 和 `current_step`。
- 第一次输入新主题时生成三步学习计划，并讲第 1 步。
- 同一个 `thread_id` 后续输入空内容、`继续`、`继续学习`、`下一课` 或 `next` 时，复用已有学习计划，并讲下一步。
- 暂不接 SQLite、Postgres 或跨进程持久化；重启 `langgraph dev` 后内存会清空。

## 数据流

```text
用户输入 topic
  -> plan_topic 判断是新主题还是继续
  -> explain_topic 根据 current_step 选择学习计划中的目标
  -> route_after_lesson 决定是否进入资料工具和测验
  -> explain_topic 结束时推进 current_step
```

## 验证

- 增加测试：同一个 `thread_id` 第一次运行后 `current_step` 变成 1。
- 再用同一个 `thread_id` 输入 `继续`，应复用原主题和学习计划，并把 `current_step` 推进到 2。
- 保留已有跳过测验、工具资料和测验测试。
