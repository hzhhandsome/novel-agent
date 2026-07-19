# LLM Switching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add global runtime LLM switching with task-level model snapshots.

**Architecture:** Keep provider creation behind `provider_factory`. Add task/run model snapshot columns, expose model config API, and make generation/retry build providers from task snapshots. Add a compact frontend model config control in the top generation toolbar.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, React, TypeScript, Pytest, Vitest.

---

### Task 1: Backend Runtime Config and Snapshots

**Files:**
- Modify: `backend/app/services/provider_factory.py`
- Modify: `backend/app/models/generation.py`
- Create: `backend/alembic/versions/0003_model_config_snapshots.py`
- Modify: `backend/app/services/chapter_service.py`
- Test: `backend/tests/test_model_switching.py`

- [x] **Step 1: Write failing backend tests**

Test runtime config update, task snapshot creation, and retry snapshot reuse.

- [x] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest backend/tests/test_model_switching.py -v
```

- [x] **Step 3: Implement runtime config and model snapshot columns**

Add snapshot dataclass/functions, SQLAlchemy JSON columns, and Alembic migration.

- [x] **Step 4: Wire generation/retry to snapshots**

Task creation stores snapshot; retry uses existing snapshot; generation run stores snapshot.

- [x] **Step 5: Run focused backend tests**

Run:

```powershell
python -m pytest backend/tests/test_model_switching.py backend/tests/test_provider_factory.py backend/tests/test_generation_recovery.py -v
```

### Task 2: Backend API

**Files:**
- Modify: `backend/app/api/routes/generation.py`
- Modify: `backend/app/schemas/generation.py`
- Test: `backend/tests/test_model_switching.py`

- [x] **Step 1: Add failing API test**

Assert `GET /api/model-config` and `PUT /api/model-config` work and hide API key.

- [x] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest backend/tests/test_model_switching.py -v
```

- [x] **Step 3: Implement API**

Add request/response schemas and route handlers.

- [x] **Step 4: Run focused backend tests**

Run:

```powershell
python -m pytest backend/tests/test_model_switching.py -v
```

### Task 3: Frontend Control

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChapterEditor.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend test**

Assert model config controls show current model and saving calls `PUT /api/model-config`.

- [x] **Step 2: Run test to verify failure**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

- [x] **Step 3: Implement frontend control**

Add compact controls in the top generation toolbar and disable them during generation.

- [x] **Step 4: Run focused frontend tests**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

### Task 4: Docs, Verification, Commit

**Files:**
- Modify: `docs/modules/model-provider.md`
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-llm-switching.md`

- [x] **Step 1: Update docs**

Document runtime switch API, task snapshot behavior, and current non-persistent secret boundary.

- [x] **Step 2: Run verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

Result:

- `backend`: 28 passed.
- `frontend`: 14 passed.
- `frontend build`: passed.
- `alembic upgrade head` with a temporary SQLite database: passed.

- [ ] **Step 3: Commit and push**

```powershell
git add .
git commit -m "实现LLM平滑切换"
git push
```
