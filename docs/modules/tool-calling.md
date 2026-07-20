# Tool Calling 模块

## 模块职责

内部工具层为 Agent 节点提供受控的项目内工具调用能力。它的第一阶段目标是让节点调用正式记忆读取工具，并把调用参数、结果摘要、失败和耗时记录到生成任务快照中。

第一阶段不是 MCP server/client 实现，但注册器接口刻意保持“工具名 + 参数 + 结构化结果”的形态，方便后续暴露为 MCP tools。

## 入口文件

- `backend/app/services/tool_registry.py`：工具注册、参数校验、执行包装和审计记录。
- `backend/app/agent/chapter_graph.py`：章节生成节点调用工具并保存 `tool_calls`。
- `frontend/src/components/AgentWorkspace.tsx`：Agent 后台展示节点工具调用摘要。

## 当前工具

- `list_open_foreshadowing(project_id)`：读取项目内未回收伏笔，过滤已回收伏笔。
- `get_chapter_summary(chapter_id)`：读取指定章节摘要和基础章节信息。

## 审计记录

每次工具调用返回一个普通 dict，并写入节点 `output_snapshot.tool_calls`：

- `tool_name`
- `task_id`
- `step_name`
- `arguments`
- `status`：`completed` 或 `failed`
- `result`
- `result_summary`
- `error_type`
- `error`
- `duration_ms`

工具参数非法时不会调用业务逻辑，调用记录会以 `failed` 状态保存。工具失败不应清空已完成节点快照；节点可以根据工具失败情况选择降级到已有上下文。

## 约束

- 工具默认只读。
- 候选记忆更新只能返回候选结果，不得绕过采纳流程写正式记忆。
- 候选正文和候选摘要不能通过工具进入正式记忆检索。
- 新工具必须先定义参数校验和测试，再接入节点。
- 节点调用工具后必须把调用记录写入 `tool_calls`，前端才能回看。

## 测试方式

```powershell
python -m pytest backend/tests/test_tool_registry.py backend/tests/test_chapter_generation.py -v
npm test -- --run src/App.test.tsx -t "real generation step"
```

## 后续修改注意事项

- 如果新增会写数据的工具，必须先明确是否只是“候选写入”；正式上下文仍只能走章节采纳路径。
- 如果工具接入 MCP server，需要继续保留当前内部注册器测试，避免外部协议适配污染业务边界。
- 如果工具结果进入 prompt，必须经过上下文预算管理，不能绕过预算直接塞入提示包。
