# LangGraph 智能体学习项目

这是一个基于 LangGraph 官方脚手架改造的学习项目。当前已经进入第六阶段：`plan_topic`、`explain_topic` 和 `make_quiz` 三个节点都会调用智谱 GLM，`collect_reference` 节点会调用本地资料查询工具，并把工具结果写回 `State` 供测验节点使用。图支持通过 `thread_id` 记住学习计划和当前学习进度，并在生成学习计划后通过 `interrupt` 等待人工确认。

当前图结构如下：

```text
START
  -> plan_topic      生成学习计划
  -> review_plan     暂停，等待确认学习计划
  -> explain_topic   根据 current_step 讲解当前知识点
      ├─ skip_quiz=false -> collect_reference -> make_quiz -> END
      └─ skip_quiz=true  -> END
```

核心代码在 [src/agent/graph.py](./src/agent/graph.py)。

模型调用封装在 [src/agent/llm.py](./src/agent/llm.py)。

本地工具封装在 [src/agent/tools.py](./src/agent/tools.py)。

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

也可以直接调用图。因为当前图里有 `interrupt`，纯 Python 脚本需要自己传入 `InMemorySaver`，并用 `Command(resume=True)` 模拟人工确认：

```bash
uv run python - <<'PY'
import asyncio
from uuid import uuid4
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from agent.graph import build_graph

async def main():
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": f"study-{uuid4()}"}}
    interrupted = await graph.ainvoke({"topic": "LangGraph 智能体"}, config)
    print("等待确认：", interrupted["__interrupt__"])
    result = await graph.ainvoke(Command(resume=True), config)
    print(result)

asyncio.run(main())
PY
```

跳过测验节点：

```bash
uv run python - <<'PY'
import asyncio
from uuid import uuid4
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from agent.graph import build_graph

async def main():
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": f"study-{uuid4()}"}}
    await graph.ainvoke({
        "topic": "LangGraph 条件边",
        "skip_quiz": True,
    }, config)
    result = await graph.ainvoke(Command(resume=True), config)
    print(result)

asyncio.run(main())
PY
```

在同一个 Studio thread 里，如果上一次运行已经生成过 `quiz`，再次传入 `skip_quiz=true` 时会清空旧的测验题，避免旧状态残留造成误解。

不跳过测验时，图会先执行 `collect_reference`，把本地资料写入 `reference` 字段，再让 `make_quiz` 基于课程讲解和参考资料生成测验题。

在 Studio 里第一次输入新主题时，流程会停在 `review_plan`。你确认后再恢复运行，`explain_topic` 才会开始讲第一课。如果恢复输入是：

```json
true
```

表示直接确认原计划。如果恢复输入是：

```json
{
  "approved": true,
  "learning_plan": ["先理解 interrupt", "再学习 Command", "最后接入 Studio"]
}
```

表示确认并替换学习计划。

继续学习下一课。纯 Python 脚本直接调用图时，需要自己传入 `InMemorySaver` 来模拟 LangGraph API 的 thread 记忆：

```bash
uv run python - <<'PY'
import asyncio
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from agent.graph import build_graph

async def main():
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "study-demo"}}

    await graph.ainvoke({
        "topic": "LangGraph 记忆",
        "skip_quiz": True,
    }, config)
    first = await graph.ainvoke(Command(resume=True), config)
    print("第一次：", first["current_step"], first["first_lesson"])

    second = await graph.ainvoke({
        "topic": "继续",
        "skip_quiz": True,
    }, config)
    print("第二次：", second["current_step"], second["first_lesson"])

asyncio.run(main())
PY
```

这里的关键是两次调用使用同一个 `thread_id`。如果换成新的 `thread_id`，LangGraph 会把它当成一条新的学习线程。

在 `uv run langgraph dev` / Studio 里，不需要在 `src/agent/graph.py` 的导出图上手动配置 `InMemorySaver`。LangGraph API 会自动接管 persistence；如果导出的 `graph` 自带自定义 checkpointer，开发服务会拒绝加载。

## 下一阶段

后续可以按学习顺序继续扩展：

1. 把本地资料查询工具升级成真实文档检索或联网查询工具。
2. 把 `InMemorySaver` 换成 SQLite 或 Postgres checkpointer，学习跨进程持久化。
3. 增加更细的人工审核，例如工具调用前确认、测验发布前确认。
