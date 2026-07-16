# Auto Chapter Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add specified-count full auto generation that loops the existing single-chapter LangGraph flow, automatically accepts non-blocking chapters, and streams overall progress to the frontend.

**Architecture:** Reuse the existing `GenerationTask` table for the outer auto task with `kind="auto_chapter_generation"` and one outer `GenerationTaskStep` per chapter. Each chapter still runs the current 11-node LangGraph and records its own child `GenerationTask`; the auto task stores child task IDs, completed chapter IDs, counts, and pause/failure state in step snapshots. Frontend consumes a new auto SSE endpoint, keeps the existing Agent backstage pointed at the current child chapter task, and shows total auto progress in the editor toolbar.

**Tech Stack:** FastAPI, SQLAlchemy, LangGraph, pytest, React, TypeScript, Vitest, SSE.

---

## Files

- Create `backend/tests/test_auto_generation.py`: backend behavior tests for specified-count auto generation, child tasks, auto acceptance, SSE payload, and pause on blocking audit.
- Modify `backend/app/models/generation.py`: add `paused` to `GenerationTaskStatus`.
- Modify `backend/app/services/chapter_service.py`: add next-chapter selection/creation, auto generation streaming service, auto task snapshot helpers, and audit blocking detection.
- Modify `backend/app/api/routes/generation.py`: add request model and `POST /api/projects/{project_id}/auto-generate/stream`.
- Modify `frontend/src/types.ts`: add `AutoGenerationTask` and completed chapter progress types.
- Modify `frontend/src/api/client.ts`: add `streamAutoGenerateChapters(projectId, chapterCount, onAutoTask)`.
- Modify `frontend/src/App.tsx`: track `autoTask`, start auto generation, pass current child task into existing backstage, refresh project when stream completes.
- Modify `frontend/src/components/ChapterEditor.tsx`: replace passive full-auto text with count input and start button.
- Modify `frontend/src/App.test.tsx`: add frontend auto generation SSE test.
- Modify `docs/modules/generation-flow.md`: document the implemented auto endpoint and status boundary.

---

### Task 1: Backend Auto Generation Happy Path

**Files:**
- Create: `backend/tests/test_auto_generation.py`
- Modify: `backend/app/models/generation.py`
- Modify: `backend/app/services/chapter_service.py`
- Modify: `backend/app/api/routes/generation.py`

- [ ] **Step 1: Write failing backend API test**

Add `backend/tests/test_auto_generation.py`:

```python
def test_auto_generate_stream_accepts_requested_chapters(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"},
    ).json()

    response = client_with_db.post(
        f"/api/projects/{project['id']}/auto-generate/stream",
        json={"chapter_count": 2},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    text = response.text
    assert "event: auto_task" in text
    assert "event: done" in text
    assert '"kind": "auto_chapter_generation"' in text
    assert '"target_count": 2' in text
    assert '"completed_count": 2' in text
    assert '"status": "completed"' in text
    assert '"current_chapter_task"' in text

    refreshed = client_with_db.get(f"/api/projects/{project['id']}").json()
    accepted = [chapter for chapter in refreshed["chapters"] if chapter["status"] == "accepted"]
    assert len(accepted) == 2
    assert all(chapter["content"] for chapter in accepted)
    assert all(chapter["summary"] for chapter in accepted)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_auto_generation.py::test_auto_generate_stream_accepts_requested_chapters -v
```

Expected: FAIL with `404` because the auto endpoint does not exist.

- [ ] **Step 3: Implement minimal backend happy path**

Add `paused = "paused"` to `GenerationTaskStatus`.

In `backend/app/services/chapter_service.py`, add:

- `stream_auto_generate_chapters(session, project_id, chapter_count, provider=None) -> Iterator[dict]`
- `_get_or_create_next_chapter(session, project_id) -> Chapter`
- `_create_auto_step(session, auto_task, chapter, index, target_count) -> GenerationTaskStep`
- `_complete_auto_step(...)`
- `_auto_task_to_dict(...)`

The service must:

1. Create `GenerationTask(project_id=project_id, chapter_id=None, kind="auto_chapter_generation")`.
2. Yield the initial snapshot.
3. For each requested chapter, create an outer step named `auto_chapter_<index>`.
4. Run `stream_chapter_generation_candidate()` and yield after each child task snapshot.
5. If no blocking audit finding exists, call `accept_chapter_candidate()`.
6. Mark the outer step completed with chapter ID, chapter number, child task ID, and accepted flag.
7. Mark the auto task completed after `chapter_count` accepted chapters.

In `backend/app/api/routes/generation.py`, add:

```python
class AutoGenerateRequest(BaseModel):
    chapter_count: int
```

and a streaming route:

```python
@router.post("/api/projects/{project_id}/auto-generate/stream")
def auto_generate_chapters_stream(project_id: int, payload: AutoGenerateRequest, session: Session = Depends(get_session)) -> StreamingResponse:
    def events():
        for task in stream_auto_generate_chapters(session, project_id, payload.chapter_count):
            yield "event: auto_task\n"
            yield f"data: {json.dumps(task, ensure_ascii=False)}\n\n"
        yield "event: done\n"
        yield "data: {}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
python -m pytest backend/tests/test_auto_generation.py::test_auto_generate_stream_accepts_requested_chapters -v
```

Expected: PASS.

---

### Task 2: Backend Pause On Blocking Audit

**Files:**
- Modify: `backend/tests/test_auto_generation.py`
- Modify: `backend/app/services/chapter_service.py`

- [ ] **Step 1: Write failing service test**

Append to `backend/tests/test_auto_generation.py`:

```python
from app.services.chapter_service import stream_auto_generate_chapters
from app.services.model_provider import MockModelProvider, ReviewFindingDraft


class BlockingReviewProvider(MockModelProvider):
    def review_chapter(self, content: str, prompt_package: str) -> list[ReviewFindingDraft]:
        return [
            ReviewFindingDraft(
                problem_type="blocking_consistency",
                message="本章偏离主线，不能自动采纳。",
                suggestion="重生成本章。",
                blocking=True,
            )
        ]


def test_auto_generate_pauses_when_audit_is_blocking(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个邮差给梦境投递真实信件"},
    ).json()

    session_override = next(iter(client_with_db.app.dependency_overrides.values()))
    with next(session_override()) as session:
        snapshots = list(
            stream_auto_generate_chapters(
                session,
                project["id"],
                chapter_count=2,
                provider=BlockingReviewProvider(),
            )
        )

    final = snapshots[-1]
    assert final["status"] == "paused"
    assert final["completed_count"] == 0
    assert final["error_type"] == "BlockingAudit"
    assert "不能自动采纳" in final["error_message"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_auto_generation.py::test_auto_generate_pauses_when_audit_is_blocking -v
```

Expected: FAIL because blocking audit is not detected or `paused` is not emitted.

- [ ] **Step 3: Implement blocking audit pause**

Add `_task_has_blocking_audit(task) -> tuple[bool, str | None]` in `chapter_service.py`. It must inspect the child task `audit_prose.output_snapshot.audit_result.findings` and return true when any finding has `blocking=True`.

In the auto loop, after the child generation completes and before `accept_chapter_candidate()`:

- If blocking, mark the outer chapter step failed.
- Set auto task status to `GenerationTaskStatus.paused`.
- Set `error_type="BlockingAudit"` and `error_message` to the first blocking message.
- Yield final snapshot and stop the iterator.

- [ ] **Step 4: Run backend auto tests**

Run:

```powershell
python -m pytest backend/tests/test_auto_generation.py -v
```

Expected: both tests PASS.

---

### Task 3: Frontend Auto SSE Client And UI

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/ChapterEditor.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing frontend test**

Append to `frontend/src/App.test.tsx`:

```typescript
  it("runs specified-count auto generation and shows total progress", async () => {
    const encoder = new TextEncoder();
    const childTask = {
      id: 21,
      project_id: 42,
      chapter_id: 100,
      kind: "chapter_generation",
      status: "completed",
      current_step: "persist_candidate_result",
      error_type: null,
      error_message: null,
      chapter: makeProject().chapters[0],
      steps: [
        {
          id: 1,
          task_id: 21,
          name: "generate_prose",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { generated_content: "全自动生成的正文。" },
          error_message: null,
        },
        {
          id: 2,
          task_id: 21,
          name: "persist_candidate_result",
          status: "completed",
          input_snapshot: {},
          output_snapshot: { persistence_result: { saved_candidate: true } },
          error_message: null,
        },
      ],
    };
    const autoTask = {
      id: 30,
      project_id: 42,
      kind: "auto_chapter_generation",
      status: "completed",
      current_step: "auto_chapter_1",
      error_type: null,
      error_message: null,
      target_count: 1,
      completed_count: 1,
      current_chapter_id: 100,
      current_chapter_task: childTask,
      completed_chapters: [{ id: 100, number: 1, title: "异常出现" }],
      steps: [],
    };

    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url === "/api/projects") {
        return Promise.resolve(new Response(JSON.stringify([makeProjectWithoutGeneratedContent()]), { status: 200 }));
      }
      if (url === "/api/projects/42/auto-generate/stream") {
        const body = new ReadableStream({
          start(controller) {
            controller.enqueue(encoder.encode(`event: auto_task\ndata: ${JSON.stringify(autoTask)}\n\n`));
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

    fireEvent.change(screen.getByLabelText("自动生成章数"), { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "开始全自动" }));

    expect(await screen.findByText("全自动：1 / 1")).toBeInTheDocument();
    expect(await screen.findByText("全自动生成的正文。")).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: FAIL because the auto count input, button, client function, and auto progress state do not exist.

- [ ] **Step 3: Implement frontend minimal auto UI**

Add types:

```typescript
export interface AutoGenerationCompletedChapter {
  id: number;
  number: number;
  title: string;
}

export interface AutoGenerationTask {
  id: number;
  project_id: number;
  kind: "auto_chapter_generation";
  status: string;
  current_step: string | null;
  error_type: string | null;
  error_message: string | null;
  target_count: number;
  completed_count: number;
  current_chapter_id: number | null;
  current_chapter_task: GenerationTask | null;
  completed_chapters: AutoGenerationCompletedChapter[];
  steps: GenerationStep[];
}
```

Add `streamAutoGenerateChapters(projectId, chapterCount, onAutoTask)` in `client.ts`, mirroring `streamGenerateChapter()` but posting JSON `{ chapter_count: chapterCount }` and parsing `auto_task` payloads.

In `App.tsx`:

- Add `autoChapterCount` state default `"3"`.
- Add `autoTask` state.
- Add `handleAutoGenerate()` that calls `streamAutoGenerateChapters(project.id, Number(autoChapterCount), setAutoTask)`.
- When each auto task arrives, call `setTask(auto.current_chapter_task)` if present.
- Pass `task={autoTask?.current_chapter_task ?? task}` to `AgentWorkspace`.
- Pass auto props to `ChapterEditor`.

In `ChapterEditor.tsx`:

- Add a compact number input labeled `自动生成章数`.
- Add button `开始全自动`.
- Show `全自动：completed / target` when an auto task exists.

- [ ] **Step 4: Run frontend test**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: PASS.

---

### Task 4: Documentation And Verification

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/superpowers/plans/2026-07-16-auto-chapter-generation.md`

- [ ] **Step 1: Update module docs**

In `docs/modules/generation-flow.md`, add the implemented endpoint:

```markdown
### 指定章数全自动生成

`POST /api/projects/{project_id}/auto-generate/stream` 返回 `text/event-stream`。

外层任务 `kind` 为 `auto_chapter_generation`，负责记录目标章数、已完成章数、当前章节任务、已自动采纳章节和暂停/失败原因。当前章节仍通过子 `chapter_generation` 任务展示 11 节点进度。
```

- [ ] **Step 2: Run full verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

Expected:

- Backend tests PASS.
- Frontend tests PASS.
- Production build PASS.

- [ ] **Step 3: Commit and push**

Run:

```powershell
git status --short
git add backend frontend docs
git commit -m "实现指定章数全自动生成"
git push
```

Expected: commit and push succeed.

---

## Self-Review

- Spec coverage: The plan implements specified-count stopping, backend-owned loop, reuse of existing 11-node LangGraph, automatic accept through the existing accept service, SSE total progress plus current child node progress, pause on blocking audit, and frontend controls.
- Scope control: The plan does not implement AI completion judgment, total-word-count stopping, automatic rewrite, complex rollback, or concurrent auto tasks.
- Type consistency: Backend uses `auto_chapter_generation`, `chapter_count`, `completed_count`, `target_count`, `current_chapter_task`, and `completed_chapters`; frontend types and tests use the same names.

## Implementation Result

- Added backend `POST /api/projects/{project_id}/auto-generate/stream`.
- Added outer `auto_chapter_generation` tasks using existing `GenerationTask` and per-chapter outer steps.
- Kept every chapter generation on the existing 11-node `chapter_generation` LangGraph.
- Added auto acceptance only after `audit_prose` has no blocking finding.
- Added `paused` task status for blocking audit pauses.
- Added frontend auto chapter count input and `开始全自动` action in the top generation toolbar.
- Auto SSE updates the current child chapter task so the existing Agent backstage shows live 11-node progress.

Focused verification run so far:

- `python -m pytest backend/tests/test_auto_generation.py -v`: 2 passed.
- `npm test -- --run src/App.test.tsx`: 10 passed.

Final verification:

- `python -m pytest -v` from repository root: failed during collection because root-level import path does not include `backend/app`.
- `python -m pytest -v` from `backend`: 16 passed.
- `npm test -- --run` from `frontend`: 10 passed.
- `npm run build` from `frontend`: passed.
