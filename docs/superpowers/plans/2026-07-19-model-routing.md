# Model Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add P0 model routing for generation, audit, and summary nodes.

**Architecture:** Extend `provider_factory` runtime config with route overrides and freeze them in task snapshots. Let `chapter_graph` choose a provider per routed node while non-routed nodes use the default task provider. Expose route model fields in the existing frontend toolbar.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy JSON snapshots, LangGraph, React, TypeScript, Pytest, Vitest.

---

### Task 1: Backend Route Config

**Files:**
- Modify: `backend/app/services/provider_factory.py`
- Modify: `backend/app/schemas/generation.py`
- Modify: `backend/app/api/routes/generation.py`
- Test: `backend/tests/test_model_switching.py`

- [x] **Step 1: Write failing API tests**

Assert route config is accepted by `PUT /api/model-config`, returned by `GET /api/model-config`, and does not expose API keys.

- [x] **Step 2: Implement runtime route config**

Add route snapshot helpers and route override merge behavior.

- [x] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest backend/tests/test_model_switching.py -v
```

### Task 2: LangGraph Provider Routing

**Files:**
- Modify: `backend/app/agent/chapter_graph.py`
- Modify: `backend/app/agent/state.py`
- Modify: `backend/app/services/chapter_service.py`
- Test: `backend/tests/test_model_routing.py`

- [x] **Step 1: Write failing routing tests**

Assert `generate_prose`, `audit_prose`, and `summarize_chapter` call route-specific providers and write route snapshots.

- [x] **Step 2: Implement route-aware graph provider selection**

Route only the three P0 nodes. Keep other nodes on the default provider.

- [x] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest backend/tests/test_model_routing.py backend/tests/test_model_switching.py -v
```

### Task 3: Frontend Route Controls

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChapterEditor.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend test**

Assert route model fields save through `PUT /api/model-config`.

- [x] **Step 2: Implement compact route fields**

Add generation/audit/summary model fields that inherit default provider/base URL/max tokens.

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
- Modify: `docs/superpowers/plans/2026-07-19-model-routing.md`

- [x] **Step 1: Update docs**

Document route keys, fallback behavior, snapshots, and UI scope.

- [x] **Step 2: Run verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

Result:

- `backend`: 32 passed.
- `frontend`: 16 passed.
- `frontend build`: passed.

- [ ] **Step 3: Commit and push**

```powershell
git add .
git commit -m "实现模型路由"
git push
```
