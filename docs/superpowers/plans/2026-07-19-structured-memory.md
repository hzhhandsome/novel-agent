# Structured Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add P0 structured memory for character periods, story events, and world rules.

**Architecture:** Extend the existing SQLAlchemy/Pydantic project model and keep formal memory writes behind the accept path. The LangGraph remains 11 nodes; `load_context` reads the new memory, while `persist_candidate_result` still only saves candidates.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, LangGraph, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Structured Memory Data

**Files:**
- Modify: `backend/app/models/character.py`
- Create: `backend/app/models/memory.py`
- Modify: `backend/app/models/project.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/schemas/project.py`
- Modify: `backend/app/repositories/projects.py`
- Test: `backend/tests/test_structured_memory.py`

- [x] **Step 1: Write failing tests**

Add assertions that project creation returns `period_stage`, `period_summary`, and baseline `world_rules`.

- [x] **Step 2: Run tests to verify failure**

Run `python -m pytest backend/tests/test_structured_memory.py -v`.

- [x] **Step 3: Implement model, schema, and seed changes**

Add character period columns, story event/world rule models, project relationships, read schemas, and project seed initialization.

- [x] **Step 4: Run focused backend tests**

Run `python -m pytest backend/tests/test_structured_memory.py -v`.

### Task 2: Generation Flow Memory Integration

**Files:**
- Modify: `backend/app/agent/chapter_graph.py`
- Modify: `backend/app/services/chapter_service.py`
- Test: `backend/tests/test_structured_memory.py`
- Test: `backend/tests/test_chapter_generation.py`
- Test: `backend/tests/test_auto_generation.py`

- [x] **Step 1: Write failing tests**

Assert `load_context` includes character period fields, story events, and world rules; accepting a chapter creates story events and updates character period summary.

- [x] **Step 2: Run tests to verify failure**

Run `python -m pytest backend/tests/test_chapter_generation.py backend/tests/test_auto_generation.py -v`.

- [x] **Step 3: Implement context loading and accept-path memory commit**

Load structured memory into `context_package`, and write official memory only in `accept_chapter_candidate()`.

- [x] **Step 4: Run focused backend tests**

Run `python -m pytest backend/tests/test_chapter_generation.py backend/tests/test_auto_generation.py -v`.

### Task 3: Frontend Structured Memory Display

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/ModulePanel.tsx`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing tests**

Assert module panel and Agent context tab display character period, story events, and world rules.

- [x] **Step 2: Run tests to verify failure**

Run `npm test -- --run src/App.test.tsx`.

- [x] **Step 3: Implement TypeScript types and UI display**

Add structured memory types and display sections.

- [x] **Step 4: Run focused frontend tests**

Run `npm test -- --run src/App.test.tsx`.

### Task 4: Docs, Verification, Commit

**Files:**
- Create: `docs/modules/memory-system.md`
- Modify: `docs/modules/index.md`
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-structured-memory.md`

- [x] **Step 1: Update module docs and roadmap status**

Document structured memory responsibilities and mark the P0 item as completed.

- [x] **Step 2: Run full verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

- [ ] **Step 3: Commit and push**

Commit with Chinese message and push.

```powershell
git add .
git commit -m "实现结构化记忆基础能力"
git push
```

## Implementation Result

- Added character period fields to `Character`.
- Added `StoryEvent` and `WorldRule` models, API schemas, TypeScript types, and Alembic migration `0002_structured_memory`.
- Project creation initializes character period state and a baseline world rule.
- `load_context` now includes character periods, event timeline, and world rules.
- Chapter acceptance writes formal structured memory through the accept path, not the candidate persistence node.
- Module panel and Agent backstage context display structured memory.
- Roadmap marks structured memory basic capability as completed.

## Verification

- RED: `python -m pytest backend/tests/test_structured_memory.py -v` failed before implementation because `period_stage` was missing and accepted chapters did not create story events.
- RED: `npm test -- --run src/App.test.tsx` failed before frontend implementation because structured memory was not displayed.
- Migration: `python -m alembic upgrade head` passed against a temporary SQLite database.
- Backend full test: `python -m pytest -v` from `backend/` passed: 20 tests passed.
- Frontend full test: `npm test -- --run` passed: 13 tests passed.
- Frontend build: `npm run build` passed.
