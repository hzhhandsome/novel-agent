# Tool Calling Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-stage internal Tool Calling layer with schema validation, audited calls, and Agent backstage visibility.

**Architecture:** Introduce a backend `ToolRegistry` that exposes read-only project tools and returns structured call records. Wire the registry into `load_context` and `judge_foreshadowing` so tool usage is recorded in node output snapshots without changing the 11-node LangGraph flow or writing formal memory outside the adoption path. Frontend reads `tool_calls` from node snapshots and displays tool name, status, arguments summary, result summary, errors, and duration.

**Tech Stack:** FastAPI service layer, SQLAlchemy session-backed queries, existing JSON node snapshots, Vitest/pytest, React TypeScript Agent workspace.

---

## Context Read

- Read `docs/modules/generation-flow.md`: generation must remain 11 LangGraph nodes; `persist_candidate_result` must not write formal memory.
- Read `docs/modules/retrieval.md`: retrieval sources must be formal memory only; candidates must not pollute vector memory.

## File Structure

- Create `backend/app/services/tool_registry.py`: defines tool schema metadata, validation, execution wrapper, call record shape, and built-in read-only tools.
- Modify `backend/app/agent/state.py`: add `tool_calls` to `ChapterGenerationState` snapshots.
- Modify `backend/app/agent/chapter_graph.py`: use registry inside `load_context` and `judge_foreshadowing`; merge tool call records into node output snapshots.
- Create `backend/tests/test_tool_registry.py`: unit tests for schema validation, read-only tool output, and failed validation audit records.
- Modify `backend/tests/test_chapter_generation.py`: generation task snapshots include tool call records.
- Modify `frontend/src/components/AgentWorkspace.tsx`: show node tool calls in active node details.
- Modify `docs/modules/generation-flow.md`: document tool-call snapshot contract.
- Modify or create `docs/modules/tool-calling.md`: document module responsibility, tools, audit shape, and constraints.

## Scope Decisions

- No new DB table in first stage; audit records live in `GenerationTaskStep.output_snapshot.tool_calls`, so existing task persistence and SSE already carry them.
- No external MCP server/client in first stage; registry API is intentionally compatible with future MCP exposure.
- Tools are read-only except `propose_memory_update`, which returns a candidate object and never writes formal memory.
- First integration points are `load_context` and `judge_foreshadowing`; later nodes can call tools through the same registry.

### Task 1: Tool Registry Core

**Files:**
- Create: `backend/app/services/tool_registry.py`
- Test: `backend/tests/test_tool_registry.py`

- [x] **Step 1: Write failing validation and audit tests**

Add tests:

```python
from app.services.tool_registry import ToolCallValidationError, get_internal_tool_registry


def test_tool_registry_rejects_missing_required_argument(client_with_db):
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)
    try:
        registry = get_internal_tool_registry(session)
        record = registry.call("list_open_foreshadowing", {"project_id": None}, task_id=1, step_name="load_context")
    finally:
        session_generator.close()

    assert record["status"] == "failed"
    assert record["tool_name"] == "list_open_foreshadowing"
    assert record["error_type"] == "ToolCallValidationError"
    assert "project_id" in record["error"]
    assert record["duration_ms"] >= 0


def test_list_open_foreshadowing_returns_read_only_summary(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一个失忆修书人修补会改变现实的书"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)
    try:
        registry = get_internal_tool_registry(session)
        record = registry.call(
            "list_open_foreshadowing",
            {"project_id": project["id"]},
            task_id=1,
            step_name="judge_foreshadowing",
        )
    finally:
        session_generator.close()

    assert record["status"] == "completed"
    assert record["tool_name"] == "list_open_foreshadowing"
    assert record["result_summary"]
    assert "items" in record["result"]
    assert record["duration_ms"] >= 0
```

- [x] **Step 2: Run tests and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_tool_registry.py -v
```

Expected: fail because `app.services.tool_registry` does not exist.

- [x] **Step 3: Implement minimal ToolRegistry**

Create `backend/app/services/tool_registry.py` with:

```python
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.foreshadowing import ForeshadowingStatus


class ToolCallValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required: tuple[str, ...]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self, specs: dict[str, ToolSpec]) -> None:
        self._specs = specs

    def call(self, tool_name: str, arguments: dict[str, Any], task_id: int | None, step_name: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            spec = self._specs[tool_name]
            self._validate(spec, arguments)
            result = spec.handler(arguments)
            return _record(tool_name, arguments, task_id, step_name, "completed", result, "", "", started)
        except Exception as exc:
            return _record(tool_name, arguments, task_id, step_name, "failed", {}, type(exc).__name__, str(exc), started)

    def _validate(self, spec: ToolSpec, arguments: dict[str, Any]) -> None:
        for key in spec.required:
            if arguments.get(key) in (None, ""):
                raise ToolCallValidationError(f"missing required argument: {key}")


def get_internal_tool_registry(session: Session) -> ToolRegistry:
    def list_open_foreshadowing(arguments: dict[str, Any]) -> dict[str, Any]:
        project_id = int(arguments["project_id"])
        items = [
            {
                "id": item.id,
                "content": item.content,
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "notes": item.notes,
            }
            for item in session.query(__import__("app.models.foreshadowing", fromlist=["ForeshadowingItem"]).ForeshadowingItem)
            .filter_by(project_id=project_id)
            .all()
            if item.status != ForeshadowingStatus.resolved
        ]
        return {"items": items, "count": len(items)}

    def get_chapter_summary(arguments: dict[str, Any]) -> dict[str, Any]:
        chapter = session.get_one(Chapter, int(arguments["chapter_id"]))
        return {"chapter_id": chapter.id, "number": chapter.number, "title": chapter.title, "summary": chapter.summary}

    return ToolRegistry(
        {
            "list_open_foreshadowing": ToolSpec(
                name="list_open_foreshadowing",
                description="Read open foreshadowing items for a project.",
                required=("project_id",),
                handler=list_open_foreshadowing,
            ),
            "get_chapter_summary": ToolSpec(
                name="get_chapter_summary",
                description="Read an accepted chapter summary.",
                required=("chapter_id",),
                handler=get_chapter_summary,
            ),
        }
    )
```

Then replace the dynamic import with a normal import before committing:

```python
from app.models.foreshadowing import ForeshadowingItem, ForeshadowingStatus
```

- [x] **Step 4: Run tests and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_tool_registry.py -v
```

Expected: both tests pass.

### Task 2: Wire Tools Into Generation Snapshots

**Files:**
- Modify: `backend/app/agent/state.py`
- Modify: `backend/app/agent/chapter_graph.py`
- Test: `backend/tests/test_chapter_generation.py`

- [x] **Step 1: Write failing generation snapshot test**

Add assertions in `test_generate_chapter_records_steps_and_generated_content`:

```python
load_context_calls = load_context.output_snapshot["tool_calls"]
assert any(call["tool_name"] == "list_open_foreshadowing" for call in load_context_calls)
assert all(call["status"] == "completed" for call in load_context_calls)

foreshadowing_step = next(step for step in task.steps if step.name == "judge_foreshadowing")
foreshadowing_calls = foreshadowing_step.output_snapshot["tool_calls"]
assert any(call["tool_name"] == "list_open_foreshadowing" for call in foreshadowing_calls)
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_records_steps_and_generated_content -v
```

Expected: fail with missing `tool_calls`.

- [x] **Step 3: Add state and node integration**

Add to `ChapterGenerationState`:

```python
tool_calls: list[dict]
```

Add `"tool_calls"` to `_snapshot_state`.

In `_load_context`, create registry and record calls:

```python
registry = get_internal_tool_registry(session)
tool_calls = [
    registry.call("list_open_foreshadowing", {"project_id": project.id}, state.get("task_id"), "load_context")
]
```

Use the completed tool result as the source for `foreshadowing_candidates`; if the call fails, fall back to the existing relationship query so generation still runs.

In `_judge_foreshadowing`, call the same tool and return `tool_calls` in output snapshot. Use the returned items to build `existing` when available; otherwise fall back to `context_package.foreshadowing_items`.

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_records_steps_and_generated_content -v
```

Expected: pass.

### Task 3: Frontend Tool Call Display

**Files:**
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend assertion**

In the real generation step fixture, add a `tool_calls` array to a node output:

```ts
tool_calls: [
  {
    tool_name: "list_open_foreshadowing",
    status: "completed",
    arguments: { project_id: 1 },
    result_summary: "count=1",
    duration_ms: 2,
  },
],
```

Add assertion:

```ts
expect(screen.getByText("工具调用")).toBeInTheDocument();
expect(screen.getByText(/list_open_foreshadowing/)).toBeInTheDocument();
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "real generation step"
```

Expected: fail because Agent workspace does not render tool calls.

- [x] **Step 3: Render tool calls**

Add helper:

```ts
function formatToolCalls(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value
    .map((call) => {
      if (!call || typeof call !== "object" || Array.isArray(call)) return "";
      const item = call as Record<string, unknown>;
      return [
        stringifyValue(item.tool_name),
        stringifyValue(item.status),
        stringifyValue(item.arguments),
        stringifyValue(item.result_summary),
        stringifyValue(item.error),
        stringifyValue(item.duration_ms) ? `${stringifyValue(item.duration_ms)}ms` : "",
      ]
        .filter(Boolean)
        .join("；");
    })
    .filter(Boolean)
    .join("\n");
}
```

In `stepHighlights`, after Prompt version:

```ts
const toolCallText = formatToolCalls(output.tool_calls);
if (toolCallText) items.push(["工具调用", toolCallText]);
```

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "real generation step"
```

Expected: pass.

### Task 4: Module Docs And Verification

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Create: `docs/modules/tool-calling.md`

- [x] **Step 1: Document the tool snapshot contract**

In `generation-flow.md`, add:

```markdown
### Tool Calling 第一阶段

`load_context` 和 `judge_foreshadowing` 可以通过内部 `ToolRegistry` 调用只读项目工具。工具调用结果写入当前节点 `output_snapshot.tool_calls`，字段包括 `tool_name`、`arguments`、`status`、`result_summary`、`error_type`、`error` 和 `duration_ms`。
```

- [x] **Step 2: Create module doc**

Create `docs/modules/tool-calling.md` with responsibilities, entry file, supported tools, audit shape, test commands, and constraints:

```markdown
# Tool Calling 模块

## 模块职责

内部工具层为 Agent 节点提供受控的项目内工具调用能力。

## 入口文件

- `backend/app/services/tool_registry.py`
- `backend/app/agent/chapter_graph.py`
- `frontend/src/components/AgentWorkspace.tsx`

## 约束

- 第一阶段不启动 MCP server。
- 工具默认只读。
- 候选记忆更新只能返回候选结果，不得绕过采纳流程写正式记忆。
```

- [x] **Step 3: Run targeted verification**

Run:

```powershell
cd backend
python -m pytest tests/test_tool_registry.py tests/test_chapter_generation.py tests/test_retrieval.py -v
cd ..\frontend
npm test -- --run src/App.test.tsx -t "real generation step"
```

Expected: backend tests pass; frontend targeted test passes.

- [ ] **Step 4: Commit code changes**

Stage only tool-calling related files and commit:

```powershell
git add backend/app/services/tool_registry.py backend/app/agent/state.py backend/app/agent/chapter_graph.py backend/tests/test_tool_registry.py backend/tests/test_chapter_generation.py frontend/src/components/AgentWorkspace.tsx frontend/src/App.test.tsx docs/modules/generation-flow.md docs/modules/tool-calling.md docs/superpowers/plans/2026-07-20-tool-calling-registry.md
git commit -m "新增内部工具调用审计"
```

Push only if network is available:

```powershell
git push
```

## Self-Review

- Spec coverage: schema validation, permissions boundary, call records, failure records, duration, backstage display, formal-memory write boundary are covered. MCP server is explicitly deferred.
- Placeholder scan: no task contains TBD/TODO or unspecified implementation.
- Type consistency: backend call record uses `tool_calls`; frontend reads the same `output.tool_calls` field.
