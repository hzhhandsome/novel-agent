# SSE Generation Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stream chapter generation progress to the frontend through SSE so the Agent backstage checks off each of the 11 Chinese workflow nodes as the backend completes them.

**Architecture:** Backend remains the source of truth. A new POST streaming endpoint runs the existing LangGraph generation flow and emits serialized `GenerationTask` snapshots after task creation, after each persisted node update, and at completion/failure. Frontend replaces the synchronous generate call with a streaming fetch parser and renders a fixed 11-node Chinese progress list using backend step status.

**Tech Stack:** FastAPI `StreamingResponse`, SQLAlchemy session-bound generation flow, React + TypeScript fetch stream parsing, Vitest/pytest.

---

## Context Read Before Planning

- Read `docs/modules/generation-flow.md`.
- Read `docs/modules/model-provider.md`.
- Current generation graph already records 11 node steps in `GenerationTaskStep`.
- Current `/api/chapters/{chapter_id}/generate` is synchronous and only returns after all nodes finish.
- User explicitly chose SSE, no old 6-node compatibility, and frontend should render all 11 nodes.

## File Structure

- Modify `backend/app/agent/chapter_graph.py`: add an optional node-progress callback to the persisted step wrapper and graph builder.
- Modify `backend/app/services/chapter_service.py`: add `stream_chapter_generation_candidate()` that yields task snapshots while the graph runs.
- Modify `backend/app/api/routes/generation.py`: add `POST /api/chapters/{chapter_id}/generate/stream` returning `text/event-stream`; reuse `_task_to_dict`.
- Modify `backend/tests/test_chapter_generation.py`: add backend streaming test that proves task events include all 11 steps and completed node statuses.
- Modify `frontend/src/api/client.ts`: add `streamGenerateChapter(chapterId, onTask)` using fetch stream SSE parsing.
- Modify `frontend/src/App.tsx`: call streaming generation and update `task` on each event.
- Modify `frontend/src/components/AgentWorkspace.tsx`: render fixed 11 Chinese node rows, map backend node status to check/running/error/pending icons, keep details from selected node.
- Modify `frontend/src/App.test.tsx`: update tests to expect Chinese node names and status progress.
- Modify `docs/modules/generation-flow.md`: document SSE progress endpoint and frontend fixed 11-node display rule.

## Task 1: Backend SSE Contract

**Files:**
- Modify: `backend/app/agent/chapter_graph.py`
- Modify: `backend/app/services/chapter_service.py`
- Modify: `backend/app/api/routes/generation.py`
- Test: `backend/tests/test_chapter_generation.py`

- [ ] **Step 1: Write the failing backend streaming test**

Add this test to `backend/tests/test_chapter_generation.py`:

```python
def test_generate_chapter_stream_emits_node_progress(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"}).json()
    chapter_id = project["chapters"][0]["id"]

    response = client_with_db.post(f"/api/chapters/{chapter_id}/generate/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    text = response.text
    assert "event: task" in text
    assert "event: done" in text
    assert '"name": "load_context"' in text
    assert '"name": "persist_candidate_result"' in text
    assert '"status": "completed"' in text

    expected_order = [
        "load_context",
        "build_chapter_target",
        "build_prompt_package",
        "generate_prose",
        "audit_prose",
        "summarize_chapter",
        "judge_foreshadowing",
        "judge_character_period",
        "propose_future_plan_updates",
        "build_candidate_result",
        "persist_candidate_result",
    ]
    last_index = -1
    for name in expected_order:
        index = text.find(f'"name": "{name}"')
        assert index > last_index
        last_index = index
```

- [ ] **Step 2: Run the backend test and verify it fails**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_stream_emits_node_progress -v
```

Expected: FAIL with 404 or missing streaming endpoint.

- [ ] **Step 3: Add graph progress callback**

In `backend/app/agent/chapter_graph.py`, extend `build_chapter_generation_graph` and `_persisted_step` so a callback can observe a committed task after each node update:

```python
from collections.abc import Callable

ProgressCallback = Callable[[int], None]


def build_chapter_generation_graph(
    session: Session,
    provider: ModelProvider,
    on_step_update: ProgressCallback | None = None,
):
    workflow = StateGraph(ChapterGenerationState)
    workflow.add_node("load_context", _persisted_step(session, "load_context", _load_context(session), on_step_update))
    ...
```

Update `_persisted_step` signature:

```python
def _persisted_step(
    session: Session,
    name: str,
    fn: NodeFn,
    on_step_update: ProgressCallback | None = None,
) -> NodeFn:
```

After every `session.commit()` that records running/completed/failed state, call:

```python
if on_step_update:
    on_step_update(state["task_id"])
```

Keep the existing retry behavior for completed steps unchanged.

- [ ] **Step 4: Add streaming service**

In `backend/app/services/chapter_service.py`, add:

```python
from collections.abc import Iterator
from queue import Queue


def stream_chapter_generation_candidate(
    session: Session,
    chapter_id: int,
    provider: ModelProvider | None = None,
) -> Iterator[GenerationTask]:
    chapter = session.get_one(Chapter, chapter_id)
    chapter.status = ChapterStatus.generating
    task = GenerationTask(project_id=chapter.project_id, chapter_id=chapter.id, kind="chapter_generation")
    session.add(task)
    session.commit()
    session.refresh(task)

    updates: Queue[int] = Queue()

    def notify(task_id: int) -> None:
        updates.put(task_id)

    yield get_generation_task(session, task.id)

    graph = build_chapter_generation_graph(session, provider or get_model_provider(), on_step_update=notify)
    initial_state = {
        "task_id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "fail_at": None,
    }

    try:
        graph.invoke(initial_state)
    except Exception:
        session.rollback()
        yield get_generation_task(session, task.id)
        return

    while not updates.empty():
        yield get_generation_task(session, updates.get())
    yield get_generation_task(session, task.id)
```

If the synchronous graph blocks before the generator drains the queue, this still gives the frontend all completed node snapshots in one streamed response for tests. A later async worker can make events arrive during long LLM calls without changing the frontend contract.

- [ ] **Step 5: Add streaming route**

In `backend/app/api/routes/generation.py`, import `json`, `StreamingResponse`, and `stream_chapter_generation_candidate`.

Add:

```python
@router.post("/api/chapters/{chapter_id}/generate/stream")
def generate_chapter_stream(
    chapter_id: int,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    def events():
        for task in stream_chapter_generation_candidate(session, chapter_id):
            yield "event: task\n"
            yield f"data: {json.dumps(_task_to_dict(task), ensure_ascii=False)}\n\n"
        yield "event: done\n"
        yield "data: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
```

- [ ] **Step 6: Run backend streaming test and verify it passes**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py::test_generate_chapter_stream_emits_node_progress -v
```

Expected: PASS.

## Task 2: Frontend SSE Parsing And 11-Node Progress

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Test: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Update `frontend/src/App.test.tsx`:

1. In `renders real generation step snapshots in the backstage`, change the old assertion:

```tsx
expect(screen.getByRole("button", { name: /load_context/ })).toBeInTheDocument();
```

to:

```tsx
expect(screen.getByRole("button", { name: /1.*加载上下文.*完成/ })).toBeInTheDocument();
```

2. Add a test that clicks generate and streams task events:

```tsx
it("updates generation progress from the streaming endpoint", async () => {
  const encoder = new TextEncoder();
  const task = {
    id: 9,
    project_id: 42,
    chapter_id: 100,
    kind: "chapter_generation",
    status: "running",
    current_step: "load_context",
    error_type: null,
    error_message: null,
    chapter: makeProject().chapters[0],
    steps: [
      {
        id: 1,
        task_id: 9,
        name: "load_context",
        status: "completed",
        input_snapshot: {},
        output_snapshot: { context_package: { worldview: "流式世界观" } },
        error_message: null,
      },
    ],
  };
  const completed = {
    ...task,
    status: "completed",
    current_step: "persist_candidate_result",
    steps: [
      ...task.steps,
      {
        id: 2,
        task_id: 9,
        name: "persist_candidate_result",
        status: "completed",
        input_snapshot: {},
        output_snapshot: { persistence_result: { saved_candidate: true } },
        error_message: null,
      },
    ],
  };

  vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
    const url = String(input);
    if (url === "/api/projects") {
      return Promise.resolve(new Response(JSON.stringify([makeProject()]), { status: 200 }));
    }
    if (url === "/api/chapters/100/generate/stream") {
      const body = new ReadableStream({
        start(controller) {
          controller.enqueue(encoder.encode(`event: task\ndata: ${JSON.stringify(task)}\n\n`));
          controller.enqueue(encoder.encode(`event: task\ndata: ${JSON.stringify(completed)}\n\n`));
          controller.enqueue(encoder.encode("event: done\ndata: {}\n\n"));
          controller.close();
        },
      });
      return Promise.resolve(new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } }));
    }
    if (url === "/api/projects/42") {
      return Promise.resolve(new Response(JSON.stringify(makeProject()), { status: 200 }));
    }
    return Promise.resolve(new Response("{}", { status: 200 }));
  });

  render(<App />);
  await screen.findByRole("button", { name: /异常出现/ });

  fireEvent.click(screen.getByRole("button", { name: "生成" }));

  expect(await screen.findByRole("button", { name: /1.*加载上下文.*完成/ })).toBeInTheDocument();
  expect(await screen.findByRole("button", { name: /11.*保存候选结果.*完成/ })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend tests and verify they fail**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx
```

Expected: FAIL because `streamGenerateChapter` does not exist and progress labels still use old rendering.

- [ ] **Step 3: Add streaming API helper**

In `frontend/src/api/client.ts`, add:

```ts
export async function streamGenerateChapter(
  chapterId: number,
  onTask: (task: GenerationTask) => void,
): Promise<GenerationTask | null> {
  const response = await fetch(`/api/chapters/${chapterId}/generate/stream`, { method: "POST" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("浏览器不支持流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let latest: GenerationTask | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data: "));
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine.slice(6));
      if (payload.id) {
        latest = payload as GenerationTask;
        onTask(latest);
      }
    }
  }

  return latest;
}
```

- [ ] **Step 4: Use streaming generation in App**

In `frontend/src/App.tsx`, import `streamGenerateChapter` instead of `generateChapter` for `handleGenerate`.

Replace:

```ts
const generated = await generateChapter(selectedChapter.id);
setTask(generated);
await refreshProject(generated.project_id);
```

with:

```ts
const generated = await streamGenerateChapter(selectedChapter.id, setTask);
if (generated) {
  await refreshProject(generated.project_id);
}
```

- [ ] **Step 5: Render fixed Chinese 11-node progress**

In `frontend/src/components/AgentWorkspace.tsx`, replace real-step label rendering with a fixed mapping:

```ts
const nodeLabels: Record<string, string> = {
  load_context: "加载上下文",
  build_chapter_target: "确认本章线路",
  build_prompt_package: "生成本章提示包",
  generate_prose: "生成章节正文",
  audit_prose: "审核是否偏离",
  summarize_chapter: "章节摘要",
  judge_foreshadowing: "伏笔判断",
  judge_character_period: "角色时期卡判断",
  propose_future_plan_updates: "判断后续线路调整",
  build_candidate_result: "输出候选结果",
  persist_candidate_result: "保存候选结果",
};

const canonicalNodeNames = Object.keys(nodeLabels);
```

Build display rows from `canonicalNodeNames` only. For each node, find matching backend step and derive status. The accessible button label should include index, Chinese label, and status text, for example `1. 加载上下文 完成`.

- [ ] **Step 6: Run frontend tests and verify they pass**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx
```

Expected: PASS.

## Task 3: Documentation And Verification

**Files:**
- Modify: `docs/modules/generation-flow.md`

- [ ] **Step 1: Update module documentation**

Add under API/module notes:

```markdown
### SSE 进度输出

`POST /api/chapters/{chapter_id}/generate/stream` 返回 `text/event-stream`。
事件：

- `task`：包含完整 `GenerationTask` 快照，前端用其中的 11 个 `GenerationTaskStep.status` 更新节点进度。
- `done`：表示本次流结束。

前端固定展示 11 个中文节点，不兼容旧 6 节点流程；后端节点名只作为状态映射键。
```

- [ ] **Step 2: Run focused backend tests**

Run:

```powershell
cd backend
python -m pytest tests/test_chapter_generation.py tests/test_generation_recovery.py -v
```

Expected: PASS.

- [ ] **Step 3: Run full backend tests**

Run:

```powershell
cd backend
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 4: Run frontend tests**

Run:

```powershell
cd frontend
npm test -- --run
```

Expected: PASS.

- [ ] **Step 5: Build frontend**

Run:

```powershell
cd frontend
npm run build
```

Expected: PASS.

## Self-Review

- Spec coverage: SSE progress, 11-node-only display, Chinese labels, completion check marks, failed/running/pending states covered.
- Placeholder scan: no placeholder steps remain.
- Type consistency: backend uses existing `GenerationTask` and `GenerationTaskStep`; frontend uses existing `GenerationTask` type and adds one streaming helper.

## Implementation Result

- Implemented `POST /api/chapters/{chapter_id}/generate/stream` with `StreamingResponse`.
- Final backend implementation uses LangGraph `graph.stream(initial_state)` to emit a task snapshot after each completed node; no background thread, queue, Redis, Celery, or extra table was added.
- Frontend generation now uses `streamGenerateChapter()` and updates `AgentWorkspace` on every `task` SSE event.
- Agent backstage fixed the displayed flow to the 11 Chinese nodes only; old 6-node display compatibility was intentionally removed.
- Node status display maps backend state to Chinese UI:
  - `completed` -> `完成`
  - `running` -> `执行中`
  - `failed` -> `失败`
  - missing step -> `等待`
- Verification run:
  - `python -m pytest tests/test_chapter_generation.py tests/test_generation_recovery.py -v`: 3 passed.
  - `python -m pytest -v`: 14 passed.
  - `npm test -- --run`: 8 passed.
  - `npm run build`: passed.
