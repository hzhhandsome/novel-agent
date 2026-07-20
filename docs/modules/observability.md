# Observability 模块

## 模块职责

Observability 模块负责把一次 Agent 运行转成可回看的 trace，帮助判断一次生成为什么慢、哪里失败、用了哪些上下文、调用了哪些工具、模型消耗是多少。

第一阶段 trace 是派生视图，不是新的状态源。任务恢复仍依赖 `GenerationTask`、`GenerationTaskStep` 和节点快照。

## 入口文件

- `backend/app/services/trace_builder.py`：从任务和节点快照派生 trace。
- `backend/app/api/routes/generation.py`：在 `_task_to_dict` 中返回 `trace`。
- `frontend/src/components/AgentWorkspace.tsx`：Agent 后台 `Trace` tab。
- `frontend/src/types.ts`：`TraceEvent` 和 `TaskTrace` 类型。

## 事件类型

`GenerationTask.trace.events` 当前包含：

- `task`：一次生成任务根 span。
- `step`：LangGraph 节点 span。
- `llm_call`：模型调用事件，来自 `<node>_model_usage`。
- `retrieval`：RAG 检索事件，来自 `context_package.retrieval_results`。
- `tool_call`：工具调用事件，来自 `output_snapshot.tool_calls`。
- `persistence`：候选保存事件，来自 `persistence_result`。

每个事件包含：

- `span_id`
- `parent_span_id`
- `event_type`
- `name`
- `status`
- `summary`
- `duration_ms`
- `metadata`

## 当前边界

- 不新增 trace 数据库表。
- 不接 Langfuse、LangSmith 或 OpenTelemetry。
- 不把 trace 作为恢复依据。
- 快照字段结构异常时，trace builder 应尽量跳过或降级展示，不能影响生成 API。

## 测试方式

```powershell
python -m pytest backend/tests/test_trace_builder.py backend/tests/test_chapter_generation.py -v
npm test -- --run src/App.test.tsx -t "real generation step"
```

## 后续修改注意事项

- 新增模型调用节点时，需要确认 `<node>_model_usage` 仍能被 trace builder 识别。
- 新增 RAG、Tool Calling 或持久化字段时，应同步补 trace event 映射和测试。
- 后续接外部观测平台时，应从当前 trace contract 或节点快照导出，不要替代任务快照。
