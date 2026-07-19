# Context Budget Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add rule-based context budget management to `load_context` and display budget details in the Agent backstage.

**Architecture:** Keep LangGraph's 11-node flow unchanged. Extract deterministic context budgeting helpers inside `chapter_graph.py`, use included items to build the prompt context, and expose budget metadata through existing `context_package` snapshots.

**Tech Stack:** FastAPI, SQLAlchemy, LangGraph, React, TypeScript, Pytest, Vitest.

---

### Task 1: Backend Budgeted Context

**Files:**
- Modify: `backend/app/agent/chapter_graph.py`
- Test: `backend/tests/test_context_budget.py`

- [x] **Step 1: Write failing tests**

Assert `load_context` returns `context_budget`, includes only bounded recent summaries/events/inspirations, and keeps omitted entries out of `prompt_package`.

- [x] **Step 2: Run tests to verify failure**

Run `python -m pytest backend/tests/test_context_budget.py -v`.

- [x] **Step 3: Implement budget helpers**

Add deterministic character budget helpers and apply them in `_load_context`.

- [x] **Step 4: Run focused backend tests**

Run `python -m pytest backend/tests/test_context_budget.py backend/tests/test_chapter_generation.py -v`.

### Task 2: Frontend Budget Display

**Files:**
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing test**

Assert Agent context tab displays context budget usage and omitted section summary.

- [x] **Step 2: Run test to verify failure**

Run `npm test -- --run src/App.test.tsx`.

- [x] **Step 3: Implement display**

Render budget usage and omitted content from `context_package.context_budget`.

- [x] **Step 4: Run focused frontend tests**

Run `npm test -- --run src/App.test.tsx`.

### Task 3: Docs, Verification, Commit

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/modules/memory-system.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-context-budget.md`

- [x] **Step 1: Update docs**

Record that `load_context` now uses a rule-based context budget.

- [x] **Step 2: Run verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

- [x] **Step 3: Commit and push**

```powershell
git add .
git commit -m "实现上下文预算管理"
git push
```

## Implementation Result

- Added rule-based context budgeting in `load_context`.
- Exposed budget metadata through `context_package.context_budget`.
- Displayed budget usage and omitted entries in the Agent backstage context tab.
- Added focused backend and frontend tests for budget behavior and display.

## Verification

- `python -m pytest -v` in `backend/`: 21 passed.
- `npm test -- --run` in `frontend/`: 13 passed.
- `npm run build` in `frontend/`: passed.
