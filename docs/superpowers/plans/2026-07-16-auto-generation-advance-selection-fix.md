# Auto Generation Advance Selection Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复全自动生成一章后，前端刷新回旧章节，导致用户无法继续从新章节推进的问题。

**Architecture:** 保持后端全自动生成和 LangGraph 流程不变，只修正前端项目刷新后的目标章节选择。SSE 收到的当前子任务章节应作为最终刷新时的优先章节，避免 React 闭包里的旧 `selectedChapterId` 覆盖生成结果。

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

### Task 1: Reproduce Stale Chapter Selection

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Context read: `docs/modules/generation-flow.md`

- [x] **Step 1: Write the failing test**

Add a test where the app starts on chapter 1, auto generation streams a child task for chapter 2, and the refreshed project contains chapter 2. Assert the editor selects chapter 2 and keeps the streamed/generated text.

- [x] **Step 2: Run test to verify it fails**

Run:
```powershell
npm test -- --run src/App.test.tsx
```

Expected before the fix: the new test fails because the editor stays on chapter 1 after `refreshProject()`.

### Task 2: Prefer Streamed Current Chapter On Refresh

**Files:**
- Modify: `frontend/src/App.tsx`

- [x] **Step 1: Implement minimal fix**

Extend `refreshProject()` with an optional `preferredChapterId` parameter. Use that id before the closed-over `selectedChapterId`.

- [x] **Step 2: Pass the preferred chapter id from generation flows**

For single chapter generation pass `generated.chapter_id`. For auto generation pass `generated.current_chapter_id` or the child task chapter id.

- [x] **Step 3: Run focused tests**

Run:
```powershell
npm test -- --run src/App.test.tsx
```

Expected after the fix: all App tests pass.

### Task 3: Verify And Record Result

**Files:**
- Modify: `docs/superpowers/plans/2026-07-16-auto-generation-advance-selection-fix.md`

- [x] **Step 1: Run full frontend checks**

Run:
```powershell
npm test -- --run
npm run build
```

- [x] **Step 2: Update this plan with result**

Record the implemented fix and verification output summary.

- [ ] **Step 3: Commit and push**

Run:
```powershell
git add frontend/src/App.tsx frontend/src/App.test.tsx docs/superpowers/plans/2026-07-16-auto-generation-advance-selection-fix.md
git commit -m "修复全自动生成后章节选择"
git push
```

---

## Implementation Result

- Added a regression test for the stale selection case: auto generation streams chapter 2 while the app initially has chapter 1 selected, then project refresh returns both accepted chapters.
- Updated `refreshProject()` to accept `preferredChapterId` and use it before the closed-over `selectedChapterId`.
- Passed generated chapter ids from single generation, auto generation, and retry flows.

## Verification

- RED: `npm test -- --run src/App.test.tsx` failed because the refreshed UI stayed on chapter 1 and could not find heading `Chapter Two`.
- GREEN: `npm test -- --run src/App.test.tsx` passed: 12 tests passed.
- Full frontend test: `npm test -- --run` passed: 1 test file, 12 tests passed.
- Frontend build: `npm run build` passed.
