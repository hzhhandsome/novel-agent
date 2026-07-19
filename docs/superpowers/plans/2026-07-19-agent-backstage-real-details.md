# Agent Backstage Real Details Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show real node outputs in the Agent backstage and make accepted foreshadowing decisions visible as formal project memory.

**Architecture:** Keep the existing 11-node LangGraph flow. Persist foreshadowing changes only through the accepted-chapter path, then refresh the project read model. On the frontend, keep raw JSON collapsed but render node-specific Chinese highlights from real snapshots, and keep context budget usage visible in the backstage header.

**Tech Stack:** FastAPI, SQLAlchemy, LangGraph, React, TypeScript, Vitest, Pytest.

---

### Task 1: Backend Foreshadowing Commit

**Files:**
- Modify: `backend/tests/test_structured_memory.py`
- Modify: `backend/app/services/chapter_service.py`
- Read: `docs/modules/generation-flow.md`
- Read: `docs/modules/memory-system.md`

- [x] Add a backend test that generates and accepts a chapter, then asserts `foreshadowing_items` contains the model's foreshadowing decision text.
- [x] Run `python -m pytest backend/tests/test_structured_memory.py -v` from `backend`; expect the new test to fail before implementation.
- [x] Add `_commit_foreshadowing_items(session, chapter, task)` and call it from `_commit_structured_memory`.
- [x] Map `new` to `planted`, `advanced` to `advanced`, and `resolved` to `recovered`; keep `notes` as item notes when present.
- [x] Avoid duplicate rows for the same `project_id`, `source_chapter_id`, and content.
- [x] Run `python -m pytest backend/tests/test_structured_memory.py -v`; expect pass.

### Task 2: Frontend Formal Memory Display

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/components/ModulePanel.tsx`
- Modify: `frontend/src/styles.css`
- Read: `docs/modules/memory-system.md`

- [x] Add a frontend test that renders `ModulePanel` and sees the foreshadowing record by default, including status text.
- [x] Add a frontend test that an empty project shows a useful "no foreshadowing" empty state.
- [x] Run `npm test -- --run src/App.test.tsx`; expect the new assertions to fail before implementation.
- [x] Open the foreshadowing section by default.
- [x] Render foreshadowing content, status, notes, and an empty state.
- [x] Run `npm test -- --run src/App.test.tsx`; expect pass.

### Task 3: Real Node Details and Persistent Budget Summary

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/styles.css`
- Read: `docs/modules/generation-flow.md`
- Read: `docs/modules/retrieval.md`
- Read: `docs/modules/evaluation.md`
- Read: `docs/modules/model-provider.md`

- [x] Add frontend tests that completed flow nodes show actual values for chapter target, prompt package, summary, foreshadowing decisions, character period decisions, future plan updates, and persistence result.
- [x] Add a frontend test that context budget usage appears in the backstage header when `load_context.context_budget` exists.
- [x] Run `npm test -- --run src/App.test.tsx`; expect new assertions to fail before implementation.
- [x] Replace generic node summaries with per-node extraction from `input_snapshot` / `output_snapshot`.
- [x] Keep raw snapshots collapsed under "原始输出".
- [x] Add a compact context budget pill to the backstage header.
- [x] Run `npm test -- --run src/App.test.tsx`; expect pass.

### Task 4: Documentation and Verification

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/modules/memory-system.md`
- Modify: `docs/modules/retrieval.md`
- Modify: `docs/modules/evaluation.md`
- Modify: `docs/modules/model-provider.md`
- Modify: `docs/superpowers/plans/2026-07-19-agent-backstage-real-details.md`

- [x] Update module docs with the stable facts changed by this work: formal foreshadowing commit, readable node detail display, and always-visible context budget relationship to max tokens.
- [x] Run `python -m pytest backend/tests/test_structured_memory.py -v` from `backend`.
- [x] Run `npm test -- --run` from `frontend`.
- [x] Run `npm run build` from `frontend`.
- [x] Run `git diff --check`.
- [ ] Commit with message `完善后台节点详情和伏笔记录`.
