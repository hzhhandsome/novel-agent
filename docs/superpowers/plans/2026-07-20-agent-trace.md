# Agent Trace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a derived trace tree to generation tasks and show it in the Agent backstage.

**Architecture:** Build trace data from existing `GenerationTask` and `GenerationTaskStep` snapshots in a backend service, attach it to `_task_to_dict`, and render it in a new frontend `Trace` tab. No new database table, no external observability dependency, and no change to the 11-node LangGraph flow.

**Tech Stack:** FastAPI, SQLAlchemy models, existing JSON snapshots, pytest, React TypeScript, Vitest.

---

## Context Read

- Read `docs/modules/generation-flow.md`: generation remains 11 LangGraph nodes; task snapshots are the source of recovery and display.
- Read `docs/modules/model-provider.md`: model usage fields already exist as `<node>_model_usage`.
- Read `docs/modules/retrieval.md`: RAG report lives in `context_package.retrieval_results`.
- Read `docs/modules/tool-calling.md`: tool audit lives in `output_snapshot.tool_calls`.

## File Structure

- Create `backend/app/services/trace_builder.py`: pure trace derivation from `GenerationTask`.
- Create `backend/tests/test_trace_builder.py`: unit coverage for root, step, LLM, RAG, tool, persistence, and error events.
- Modify `backend/app/api/routes/generation.py`: include `trace` in `_task_to_dict`.
- Modify `backend/tests/test_chapter_generation.py`: API response includes trace events.
- Modify `frontend/src/types.ts`: add `TraceEvent` and `TaskTrace`.
- Modify `frontend/src/components/AgentWorkspace.tsx`: add `trace` tab and trace event rendering.
- Modify `frontend/src/App.test.tsx`: verify Trace tab output.
- Modify `docs/modules/generation-flow.md`: document trace contract.
- Create `docs/modules/observability.md`: document first-stage observability module.

### Task 1: Backend Trace Builder

**Files:**
- Create: `backend/app/services/trace_builder.py`
- Test: `backend/tests/test_trace_builder.py`

- [x] **Step 1: Write failing trace builder tests**

Create tests that build a generated task through the existing API, then call `build_task_trace(task)` and assert:

```python
trace = build_task_trace(task)
assert trace["trace_id"] == f"generation-task-{task.id}"
assert any(event["event_type"] == "task" for event in trace["events"])
assert any(event["event_type"] == "step" and event["name"] == "load_context" for event in trace["events"])
assert any(event["event_type"] == "llm_call" and event["name"] == "generate_prose" for event in trace["events"])
assert any(event["event_type"] == "retrieval" for event in trace["events"])
assert any(event["event_type"] == "tool_call" for event in trace["events"])
assert any(event["event_type"] == "persistence" for event in trace["events"])
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_trace_builder.py -v
```

Expected: fail because `app.services.trace_builder` does not exist.

- [x] **Step 3: Implement trace builder**

Implement:

```python
def build_task_trace(task: GenerationTask) -> dict:
    ...
```

Rules:

- root task event always exists;
- one step event per `task.steps`;
- model usage child events from keys ending `_model_usage`;
- retrieval child event from `context_package.retrieval_results`;
- tool child events from `tool_calls`;
- persistence child event from `persistence_result`;
- failed task/step error appears in metadata and summary.

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_trace_builder.py -v
```

Expected: pass.

### Task 2: API Trace Output

**Files:**
- Modify: `backend/app/api/routes/generation.py`
- Modify: `backend/tests/test_chapter_generation.py`

- [x] **Step 1: Write failing API assertion**

In `test_generate_chapter_records_steps_and_generated_content`, assert:

```python
trace = body["trace"]
assert trace["trace_id"] == f"generation-task-{body['id']}"
assert any(event["event_type"] == "llm_call" for event in trace["events"])
assert any(event["event_type"] == "tool_call" for event in trace["events"])
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_records_steps_and_generated_content -v
```

Expected: fail with missing `trace`.

- [x] **Step 3: Add trace to `_task_to_dict`**

Import `build_task_trace` and add:

```python
"trace": build_task_trace(task),
```

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_records_steps_and_generated_content -v
```

Expected: pass.

### Task 3: Frontend Trace Tab

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend assertion**

Add a `trace` object to the real generation task fixture and assert:

```ts
fireEvent.click(screen.getByRole("tab", { name: "Trace" }));
expect(screen.getByText("Trace")).toBeInTheDocument();
expect(screen.getByText(/llm_call/)).toBeInTheDocument();
expect(screen.getByText(/generate_prose/)).toBeInTheDocument();
expect(screen.getByText(/tool_call/)).toBeInTheDocument();
```

- [x] **Step 2: Run test and verify RED**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "real generation step"
```

Expected: fail because there is no Trace tab.

- [x] **Step 3: Add types and UI rendering**

Add types:

```ts
export interface TraceEvent {
  span_id: string;
  parent_span_id: string | null;
  event_type: string;
  name: string;
  status: string;
  summary: string;
  duration_ms: number | null;
  metadata: Record<string, unknown>;
}

export interface TaskTrace {
  trace_id: string;
  root_span_id: string;
  events: TraceEvent[];
}
```

Add `trace` to `GenerationTask`.

Add `trace` to `WorkspaceTab`, a `Trace` tab button, and a simple event list rendering `event_type`, `name`, `status`, `summary`, and `duration_ms`.

- [x] **Step 4: Run test and verify GREEN**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "real generation step"
```

Expected: pass.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Create: `docs/modules/observability.md`

- [x] **Step 1: Document trace contract**

Add to generation flow docs: `GenerationTask.trace` is derived from persisted task/step snapshots and includes task, step, llm_call, retrieval, tool_call, persistence, and error events.

- [x] **Step 2: Create observability module doc**

Document responsibilities, entry files, event schema, current limitations, testing, and future Langfuse/LangSmith/OpenTelemetry extension.

- [x] **Step 3: Run targeted verification**

Run:

```powershell
cd backend
python -m pytest tests/test_trace_builder.py tests/test_chapter_generation.py tests/test_retrieval.py tests/test_tool_registry.py -v
cd ..\frontend
npm test -- --run src/App.test.tsx -t "real generation step"
```

Expected: all targeted tests pass.

- [ ] **Step 4: Commit and push**

Stage only trace-related files:

```powershell
git add backend/app/services/trace_builder.py backend/app/api/routes/generation.py backend/tests/test_trace_builder.py backend/tests/test_chapter_generation.py frontend/src/types.ts frontend/src/components/AgentWorkspace.tsx frontend/src/App.test.tsx docs/modules/generation-flow.md docs/modules/observability.md docs/superpowers/specs/2026-07-20-agent-trace-design.md docs/superpowers/plans/2026-07-20-agent-trace.md
git commit -m "新增 Agent Trace 后台视图"
git push
```

## Self-Review

- Spec coverage: trace root, step, LLM, RAG, tool, persistence, error, API output, frontend display, docs are covered.
- Placeholder scan: no placeholders remain.
- Scope check: no DB migration or external observability platform in first stage.
