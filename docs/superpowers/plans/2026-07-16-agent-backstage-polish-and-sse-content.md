# Agent Backstage Polish And SSE Content Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Polish the Agent backstage UI and show generated prose in the center editor area as soon as the `generate_prose` SSE node completes.

**Architecture:** Keep the existing single SSE task stream. The stream continues to update backstage node progress, and the frontend additionally derives a live generated-content candidate from `generate_prose.output_snapshot.generated_content`. Backstage collapse state lives in `App` so the center editor row can expand when the backstage is collapsed.

**Tech Stack:** React + TypeScript, CSS grid, Vitest, existing FastAPI SSE endpoint.

---

## Context

- Read `docs/modules/generation-flow.md`.
- Current backend already emits `GenerationTask` snapshots through `POST /api/chapters/{chapter_id}/generate/stream`.
- Current frontend fixed 11 Chinese nodes and shows status text at the right side of each node.
- User confirmed:
  - Remove visible right-side `完成/等待` text from node rows, keep only left icon.
  - Backstage must be collapsible.
  - Hide scrollbars while retaining scroll behavior.
  - Keep one SSE stream for all backend steps; when `generate_prose` completes, show its generated prose in the center content candidate area.

## Files

- Modify `frontend/src/App.tsx`: own backstage collapsed state and pass live task candidate content into `ChapterEditor`.
- Modify `frontend/src/components/AgentWorkspace.tsx`: add collapse button, remove visible status text, keep accessible status labels.
- Modify `frontend/src/components/ChapterEditor.tsx`: display live SSE generated content before project refresh persists `chapter.generated_content`.
- Modify `frontend/src/styles.css`: collapsed layout class, hidden scrollbars, no visible node status text.
- Modify `frontend/src/App.test.tsx`: tests for collapse, hidden status text, and SSE prose candidate display.
- Modify `docs/modules/generation-flow.md`: document that `generate_prose` snapshot is used for center candidate display.

## Tasks

### Task 1: Failing Tests

- Add a test that renders `AgentWorkspace` with a completed step and asserts the visible node row no longer contains right-side `完成`, while the accessible button name still includes `完成`.
- Add a test that clicks the backstage collapse button and verifies the workspace becomes collapsed.
- Add a test that streams a task with `generate_prose.output_snapshot.generated_content` and verifies the center "生成结果" shows that content before project refresh.
- Run `cd frontend; npm test -- --run src/App.test.tsx` and confirm the tests fail for the expected missing behavior.

### Task 2: Implementation

- Add `backstageCollapsed` state in `App`.
- Add `liveGeneratedContent` derived from `task.steps.find(step.name === "generate_prose")?.output_snapshot?.generated_content`.
- Pass `liveGeneratedContent` into `ChapterEditor`.
- Pass `collapsed` and `onToggleCollapsed` into `AgentWorkspace`.
- In `AgentWorkspace`, render an icon button in `backstage-bar`; when collapsed, render only the bar.
- Remove visible `.flow-node-status` text from node rows; keep `aria-label`.
- Add `.app-shell.backstage-collapsed` grid row sizing.
- Hide scrollbars using `scrollbar-width: none` and `::-webkit-scrollbar { display: none; }` on internal scroll containers.

### Task 3: Documentation And Verification

- Update `docs/modules/generation-flow.md` SSE section with `generate_prose` center candidate display rule.
- Run:
  - `cd frontend; npm test -- --run src/App.test.tsx`
  - `cd frontend; npm test -- --run`
  - `cd frontend; npm run build`
  - `cd backend; python -m pytest tests/test_chapter_generation.py tests/test_generation_recovery.py -v`

## Self-Review

- Covers all four user requests.
- Does not add token-level streaming or provider protocol changes.
- Keeps the first version scope: one SSE task stream drives both backstage progress and center candidate display.

## Implementation Result

- Removed visible right-side status text from flow nodes; accessible labels still include status.
- Added backstage collapse/expand controlled by `App`, with collapsed layout giving the editor more vertical space.
- Hid scrollbars globally while preserving scroll behavior.
- Added live generated prose display in the center candidate area from `generate_prose.output_snapshot.generated_content`.
- Updated generation-flow module documentation with the center candidate display rule.
- Verification:
  - `npm test -- --run src/App.test.tsx`: 9 passed.
  - `npm test -- --run`: 9 passed.
  - `npm run build`: passed.
  - `python -m pytest tests/test_chapter_generation.py tests/test_generation_recovery.py -v`: 3 passed.
  - `python -m pytest -v`: 14 passed.
