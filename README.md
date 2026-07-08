# LangGraph 智能体学习项目

这是一个基于 LangGraph 官方脚手架改造的学习项目。当前第一阶段实现了一个最小的“学习计划 Agent”，用于理解 LangGraph 里最核心的概念：`StateGraph`、`state`、`node` 和 `edge`。

当前图结构如下：

```text
START
  -> plan_topic      生成学习计划
  -> explain_topic   讲解第一个知识点
  -> make_quiz       生成小测验
  -> END
```

核心代码在 [src/agent/graph.py](./src/agent/graph.py)。

## 环境准备

项目使用 `uv` 管理依赖。进入项目目录后执行：

```bash
uv sync
```

如果本机默认 Python 版本过新导致依赖编译卡住，可以显式使用 Python 3.13：

```bash
uv run --python /opt/homebrew/Caskroom/miniconda/base/bin/python3.13 python -c "import sys; print(sys.version)"
```

## 本地启动

启动 LangGraph 开发服务：

```bash
uv run langgraph dev
```

启动成功后会看到类似地址：

```text
API: http://127.0.0.1:2024
Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
API Docs: http://127.0.0.1:2024/docs
```

`langgraph dev` 是开发服务器，启动后会一直占用当前终端。停止时按 `Ctrl+C`。

如果 `2024` 端口已经被占用，可以换端口：

```bash
uv run langgraph dev --port 2025
```

## 本地验证

运行测试：

```bash
uv run pytest -q
```

也可以直接调用图：

```bash
uv run python - <<'PY'
import asyncio
from agent.graph import graph

async def main():
    result = await graph.ainvoke({"topic": "LangGraph 智能体"})
    print(result)

asyncio.run(main())
PY
```

## 下一阶段

后续可以按学习顺序继续扩展：

1. 接入智谱 GLM，让 `plan_topic`、`explain_topic`、`make_quiz` 由真实模型生成。
2. 增加条件边，根据用户是否掌握知识点决定继续讲解还是进入测验。
3. 增加工具调用，让 Agent 可以查询资料。
4. 增加记忆和 checkpoint，保留每个学习线程的状态。
5. 增加 human-in-the-loop，让关键学习计划需要用户确认后再继续。
