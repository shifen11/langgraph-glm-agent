# LangGraph 智能体学习项目

这是一个基于 LangGraph 官方脚手架改造的学习项目。当前已经进入第三阶段：`plan_topic`、`explain_topic` 和 `make_quiz` 三个节点都会调用智谱 GLM，并且 `explain_topic` 后面增加了条件边，可以通过 `skip_quiz` 决定是否跳过测验节点。

当前图结构如下：

```text
START
  -> plan_topic      生成学习计划
  -> explain_topic   讲解第一个知识点
      ├─ skip_quiz=false -> make_quiz -> END
      └─ skip_quiz=true  -> END
```

核心代码在 [src/agent/graph.py](./src/agent/graph.py)。

模型调用封装在 [src/agent/llm.py](./src/agent/llm.py)。

## 环境准备

项目使用 `uv` 管理依赖。进入项目目录后执行：

```bash
uv sync
```

如果本机默认 Python 版本过新导致依赖编译卡住，可以显式使用 Python 3.13：

```bash
uv run --python /opt/homebrew/Caskroom/miniconda/base/bin/python3.13 python -c "import sys; print(sys.version)"
```

## 模型配置

复制 `.env.example` 后，在 `.env` 里配置智谱：

```text
ZHIPU_API_KEY=你的智谱 API Key
ZHIPU_ENDPOINT=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4-flash
```

当前阶段要求必须配置 `ZHIPU_API_KEY`、`ZHIPU_ENDPOINT` 和 `ZHIPU_MODEL`。如果缺少任一配置，运行图时会直接报错，方便你明确看到模型调用链路的问题。

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

跳过测验节点：

```bash
uv run python - <<'PY'
import asyncio
from agent.graph import graph

async def main():
    result = await graph.ainvoke({
        "topic": "LangGraph 条件边",
        "skip_quiz": True,
    })
    print(result)

asyncio.run(main())
PY
```

在同一个 Studio thread 里，如果上一次运行已经生成过 `quiz`，再次传入 `skip_quiz=true` 时会清空旧的测验题，避免旧状态残留造成误解。

## 下一阶段

后续可以按学习顺序继续扩展：

1. 增加工具调用，让 Agent 可以查询资料。
2. 增加记忆和 checkpoint，保留每个学习线程的状态。
3. 增加 human-in-the-loop，让关键学习计划需要用户确认后再继续。
