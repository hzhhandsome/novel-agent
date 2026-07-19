# Backstage Layout Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Agent backstage usable when Eval and generation details contain lots of content.

**Architecture:** Keep the three-column layout. Control the bottom backstage height from `App` with a CSS variable and a drag handle in `AgentWorkspace`. Render flow node snapshots as concise Chinese summaries plus a collapsed raw-output block. Keep result/update cards collapsed by default so the backstage stays scannable.

**Tech Stack:** React, TypeScript, CSS Grid, Vitest, Testing Library.

---

### Task 1: Frontend Tests

**Files:**
- Modify: `frontend/src/App.test.tsx`

- [x] Add a test that drags the backstage resize handle and asserts the app shell CSS variable changes.
- [x] Add a test that clicks the prose generation flow node and asserts raw snapshot keys are hidden until "Raw output" is opened.
- [x] Add a test that result/update details are collapsed until the user opens a specific card.
- [x] Run `npm test -- --run src/App.test.tsx` and confirm the new tests fail before the implementation.

### Task 2: Backstage Resize

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/styles.css`

- [x] Add `backstageHeight` state in `App`, default `420`.
- [x] Apply `--backstage-height` to `.app-shell`.
- [x] Add an accessible drag handle to `AgentWorkspace`.
- [x] Clamp resize height between `220` and viewport height minus `180`.
- [x] Update CSS grid rows to use `var(--backstage-height)`.

### Task 3: Collapsed Details

**Files:**
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/styles.css`

- [x] Replace raw per-key flow cards with curated Chinese highlights.
- [x] Put `input_snapshot` and `output_snapshot` JSON into one collapsed "Raw output" section.
- [x] Remove default-open behavior from result/update cards.
- [x] Ensure result cards show useful summary text while collapsed.

### Task 4: Verification

**Files:**
- All changed files

- [x] Run `npm test -- --run src/App.test.tsx`.
- [x] Run `npm test -- --run`.
- [x] Run `npm run build`.
- [x] Commit with message `整理Agent后台布局`.

### Implementation Result

- The backstage height now defaults to `420px` and can be dragged vertically from the top edge.
- Flow nodes now show concise Chinese highlights first; large JSON snapshots are hidden behind a collapsed raw-output section.
- Result/update cards are closed by default and expand only after user action.
- Eval output remains in the result/update tab, so it is not buried under expanded generation snapshots.
