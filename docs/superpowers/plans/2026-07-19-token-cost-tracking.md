# Token Cost Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-stage model call token and cost tracking for chapter generation.

**Architecture:** Add a small deterministic usage estimator service. LangGraph model-call nodes record per-node usage in output snapshots. `chapter_service` aggregates step usage into `GenerationRun.model_usage_snapshot`. Frontend Agent backstage sums and displays current task usage.

**Tech Stack:** FastAPI, SQLAlchemy JSON, Alembic, LangGraph, React, TypeScript, Pytest, Vitest.

---

### Task 1: Usage Estimator

**Files:**
- Create: `backend/app/services/model_usage.py`
- Modify: `backend/app/core/config.py`
- Test: `backend/tests/test_model_usage.py`

- [x] **Step 1: Write failing estimator tests**
- [x] **Step 2: Implement deterministic token and cost estimation**
- [x] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest backend/tests/test_model_usage.py -v
```

### Task 2: Node and Run Snapshots

**Files:**
- Modify: `backend/app/agent/chapter_graph.py`
- Modify: `backend/app/agent/state.py`
- Modify: `backend/app/models/generation.py`
- Create: `backend/alembic/versions/0004_model_usage_snapshots.py`
- Modify: `backend/app/services/chapter_service.py`
- Test: `backend/tests/test_model_usage.py`

- [x] **Step 1: Write failing graph/run tests**
- [x] **Step 2: Record usage in model-call node outputs**
- [x] **Step 3: Store aggregate usage in generation runs**
- [x] **Step 4: Run focused backend tests**

Run:

```powershell
python -m pytest backend/tests/test_model_usage.py backend/tests/test_chapter_generation.py -v
```

### Task 3: Frontend Display

**Files:**
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend test**
- [x] **Step 2: Display task usage summary in Agent backstage**
- [x] **Step 3: Run focused frontend tests**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

### Task 4: Docs, Verification, Commit

**Files:**
- Modify: `docs/modules/model-provider.md`
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-token-cost-tracking.md`

- [x] **Step 1: Update docs**
- [x] **Step 2: Run verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

Result:

- `backend`: 35 passed.
- `frontend`: 16 passed.
- `frontend build`: passed.
- `alembic upgrade head` with a temporary SQLite database: passed.

- [ ] **Step 3: Commit and push**

```powershell
git add .
git commit -m "实现成本和token统计"
git push
```
