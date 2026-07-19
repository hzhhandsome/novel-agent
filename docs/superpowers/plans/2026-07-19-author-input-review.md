# Author Input Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-stage AI review for project ideas and author inspirations.

**Architecture:** Extend `ModelProvider` with `review_user_input`. Add a small backend service/API that builds project context and uses the audit route provider. Frontend calls it before create/add actions and displays the latest result.

**Tech Stack:** FastAPI, React, TypeScript, Pytest, Vitest.

---

### Task 1: Backend Provider and API

**Files:**
- Modify: `backend/app/services/model_provider.py`
- Create: `backend/app/services/input_review.py`
- Modify: `backend/app/api/routes/projects.py`
- Test: `backend/tests/test_input_review.py`

- [x] **Step 1: Write failing backend tests**
- [x] **Step 2: Implement provider method and service**
- [x] **Step 3: Add API endpoints**
- [x] **Step 4: Run focused backend tests**

Run:

```powershell
python -m pytest backend/tests/test_input_review.py backend/tests/test_model_provider.py -v
```

### Task 2: Frontend Review Before Writes

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChapterEditor.tsx`
- Modify: `frontend/src/components/ModulePanel.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend tests**
- [x] **Step 2: Call review before create/add inspiration**
- [x] **Step 3: Display latest review result**
- [x] **Step 4: Run focused frontend tests**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

### Task 3: Docs, Verification, Commit

**Files:**
- Create: `docs/modules/author-interaction.md`
- Modify: `docs/modules/index.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-author-input-review.md`

- [x] **Step 1: Update docs**
- [x] **Step 2: Run verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

Result:

- `backend`: 37 passed.
- `frontend`: 18 passed.
- `frontend build`: passed.

- [ ] **Step 3: Commit and push**

```powershell
git add .
git commit -m "实现用户输入AI评判"
git push
```
