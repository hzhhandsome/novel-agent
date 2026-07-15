# Chapter Graph 11 Nodes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert chapter generation from the current 6-node LangGraph into an 11-node graph whose node inputs/outputs are persisted and displayed by the Agent backstage.

**Architecture:** Backend remains the source of truth. `GenerationTaskStep` continues to store node status, input snapshots, output snapshots, and errors; no new database table is required for P0. Frontend uses returned step snapshots when a task exists, and only falls back to static target-flow labels when no task has run.

**Tech Stack:** FastAPI, SQLAlchemy, LangGraph, Pydantic-style dict responses, React, TypeScript, Vitest, pytest.

---

## Scope

This plan implements process persistence and candidate-result persistence. It does not auto-accept generated content into official chapter content, and it does not mutate official character cards, foreshadowing rows, or future chapter titles yet. Those mutations should later be gated by an explicit `auto_commit_result` step or auto mode setting.

## Files

- Modify: `backend/app/agent/state.py`
  - Add fields for audit result, summary result, foreshadowing decisions, character period decisions, future plan updates, and candidate result.
- Modify: `backend/app/services/model_provider.py`
  - Add provider methods for foreshadowing, character period, and future plan decisions.
  - Keep `generate_chapter()` for prose generation, but the graph will treat its summary/update fields as draft data until later nodes confirm them.
- Modify: `backend/app/agent/chapter_graph.py`
  - Replace the 6-node graph with 11 nodes:
    `load_context`, `build_chapter_target`, `build_prompt_package`, `generate_prose`, `audit_prose`, `summarize_chapter`, `judge_foreshadowing`, `judge_character_period`, `propose_future_plan_updates`, `build_candidate_result`, `persist_candidate_result`.
  - Persist meaningful snapshots for each node.
- Modify: `backend/app/services/chapter_service.py`
  - Stop calling a separate post-graph persistence function when persistence is now a graph node.
  - Update generation-run recording to use new step names.
- Modify: `backend/app/api/routes/generation.py`
  - Include `input_snapshot` and `output_snapshot` in returned steps.
- Modify: `backend/tests/test_chapter_generation.py`
  - Assert exact 11-node order and useful output snapshots.
- Modify: `backend/tests/test_generation_recovery.py`
  - Retry should use a new node name such as `audit_prose`.
- Modify: `frontend/src/types.ts`
  - Add `input_snapshot` and `output_snapshot` to `GenerationStep`.
- Modify: `frontend/src/components/AgentWorkspace.tsx`
  - Render real task steps when present.
  - Use step output snapshots for context and result/update tabs.
  - Keep result cards split: audit, summary, foreshadowing, character, future plan, persistence.
- Modify: `frontend/src/App.test.tsx`
  - Add a focused test for real step output rendering.
- Modify: `docs/modules/generation-flow.md`
  - Update stable module facts from 6 nodes to 11 nodes.

---

## Task 1: Backend Tests For 11 Nodes And Snapshots

- [ ] Write failing tests in `backend/tests/test_chapter_generation.py`:
  - `test_generate_chapter_records_steps_and_generated_content` expects the 11-node order.
  - It checks every step has `output_snapshot`.
  - It checks `summarize_chapter` appears after `audit_prose`.
  - It checks `build_candidate_result.output_snapshot.candidate_result` contains `summary`, `audit`, `foreshadowing`, `character_period`, and `future_plan`.
- [ ] Update `backend/tests/test_generation_recovery.py` to fail at `audit_prose`.
- [ ] Run:
  ```powershell
  python -m pytest backend/tests/test_chapter_generation.py backend/tests/test_generation_recovery.py -v
  ```
  Expected before implementation: failing step-order/snapshot assertions.

## Task 2: Backend 11-Node Graph

- [ ] Extend `ChapterGenerationState` with:
  - `draft_summary`
  - `audit_result`
  - `summary_result`
  - `foreshadowing_decisions`
  - `character_period_decisions`
  - `future_plan_updates`
  - `candidate_result`
- [ ] Add provider protocol methods:
  - `judge_foreshadowing(content, context, existing_items) -> dict`
  - `judge_character_period(content, context, characters) -> dict`
  - `propose_future_plan_updates(content, context, chapters) -> dict`
- [ ] Implement these methods in `MockModelProvider` and `DeepSeekAnthropicProvider`.
- [ ] Update `chapter_graph.py`:
  - Rename `review_prose` node to `audit_prose`.
  - Split `propose_memory_updates` into dedicated nodes.
  - Add `build_candidate_result`.
  - Add `persist_candidate_result` to save generated content, candidate summary, review findings, and task completion.
- [ ] Run targeted backend tests until green.

## Task 3: API Snapshots And Frontend Real Step Rendering

- [ ] Include `input_snapshot` and `output_snapshot` in `/api/.../generate` task step response.
- [ ] Extend frontend `GenerationStep`.
- [ ] Update `AgentWorkspace`:
  - `流程节点` left list uses `task.steps` when available.
  - Right detail displays selected step `output_snapshot`.
  - `上下文` uses `load_context.output_snapshot`.
  - `结果与更新` uses `build_candidate_result.output_snapshot.candidate_result` and `persist_candidate_result.output_snapshot`.
  - Audit, summary, foreshadowing, character, future plan, and persistence remain separate cards.
- [ ] Add/adjust frontend tests and run:
  ```powershell
  cd frontend
  npm test -- --run
  npm run build
  ```

## Task 4: Docs And Full Verification

- [ ] Update `docs/modules/generation-flow.md` with 11-node flow and persistence behavior.
- [ ] Run:
  ```powershell
  python -m pytest -v
  cd frontend
  npm test -- --run
  npm run build
  ```
- [ ] Check `git status --short` and report code/doc changes without committing unless requested.

---

## Self-Review

- Covers the user's request to start development on 11 real nodes.
- Keeps foreshadowing and character period judgments separate in both backend nodes and frontend result cards.
- Does not add unrelated automatic official database mutations.
- Uses existing `GenerationTaskStep` process persistence rather than adding a new table.
