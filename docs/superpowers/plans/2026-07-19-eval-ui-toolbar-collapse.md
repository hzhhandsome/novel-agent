# Eval UI And Toolbar Collapse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show built-in Eval results in the frontend and make the top generation toolbar collapsible.

**Architecture:** Add a read-only FastAPI route that reuses the existing evaluation runner. Add frontend API types and render the report in AgentWorkspace. Keep toolbar collapse as local App state passed into ChapterEditor.

**Tech Stack:** FastAPI, pytest, React, TypeScript, Vitest, Testing Library.

---

### Task 1: Eval API

**Files:**
- Modify: `backend/tests/test_evaluation.py`
- Create: `backend/app/api/routes/evals.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing API test**

Add a test that calls `GET /api/evals/builtin` and asserts the aggregate result fields.

- [ ] **Step 2: Run backend eval test**

Run: `python -m pytest backend/tests/test_evaluation.py -v`

- [ ] **Step 3: Implement route**

Create `backend/app/api/routes/evals.py` and include it from `backend/app/main.py`.

- [ ] **Step 4: Re-run backend eval test**

Run: `python -m pytest backend/tests/test_evaluation.py -v`

### Task 2: Eval Frontend Display

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing UI test**

Mock `/api/evals/builtin`, click “运行 Eval”, and assert the Eval report appears.

- [ ] **Step 2: Run frontend test**

Run: `npm test -- --run src/App.test.tsx`

- [ ] **Step 3: Add types, client call, state and UI**

Add `EvalReport` types, `runBuiltinEvals()`, App state/handler, and AgentWorkspace report rendering.

- [ ] **Step 4: Re-run frontend test**

Run: `npm test -- --run src/App.test.tsx`

### Task 3: Collapsible Top Toolbar

**Files:**
- Modify: `frontend/src/components/ChapterEditor.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing toolbar test**

Click “收起工具栏”, assert model fields are hidden, then click “展开工具栏” and assert they return.

- [ ] **Step 2: Run frontend test**

Run: `npm test -- --run src/App.test.tsx`

- [ ] **Step 3: Implement collapse state and CSS**

Add collapse props to ChapterEditor and hide toolbar controls when collapsed.

- [ ] **Step 4: Re-run frontend test**

Run: `npm test -- --run src/App.test.tsx`

### Task 4: Verification And Commit

**Files:**
- All changed files

- [ ] **Step 1: Run backend verification**

Run: `python -m pytest -v`

- [ ] **Step 2: Run frontend verification**

Run: `npm test -- --run`

- [ ] **Step 3: Run frontend build**

Run: `npm run build`

- [ ] **Step 4: Update evaluation module doc if API changed**

Add the frontend/API entry to `docs/modules/evaluation.md`.

- [ ] **Step 5: Commit and push**

Commit message: `前端展示Eval并折叠生成工具栏`
