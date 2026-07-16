# Inline SSE Editor Lock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show generated/SSE chapter prose directly in the center chapter editor, remove the separate generated-result block, and prevent chapter text editing while generation is running.

**Architecture:** Keep backend SSE unchanged. `App` remains the state owner and synchronizes editor content from `generate_prose.output_snapshot.generated_content` and persisted `chapter.generated_content`; `ChapterEditor` becomes a single-surface editor with candidate actions in the toolbar instead of a separate result panel.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, existing FastAPI SSE contract.

---

## Files

- Modify `frontend/src/App.test.tsx`: update/add tests for inline candidate display, no generated result block, SSE-to-textarea update, and busy editor locking.
- Modify `frontend/src/App.tsx`: sync editor content from live/persisted generated candidates and keep refresh/select logic from clearing candidate content.
- Modify `frontend/src/components/ChapterEditor.tsx`: add `aria-label="章节正文"`, disable textarea while busy, move candidate accept/reject actions into toolbar, remove candidate section.
- Modify `frontend/src/styles.css`: remove unused `.candidate` block if no longer used.
- Modify `docs/modules/generation-flow.md`: update SSE display rule from separate generated result block to center editor textarea.

---

### Task 1: Inline Candidate Display

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/ChapterEditor.tsx`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing tests**

Update `frontend/src/App.test.tsx` so existing project candidate and SSE candidate must appear in the `章节正文` textarea, and the `生成结果` region must not exist.

- [ ] **Step 2: Run failing test**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: FAIL because `章节正文` label and inline candidate display do not exist.

- [ ] **Step 3: Implement inline candidate display**

Add `aria-label="章节正文"` to the chapter textarea. In `App`, set editor content from `chapter.content ?? chapter.generated_content ?? ""` when selecting/loading/refreshing chapters. Add an effect that copies live SSE generated content into `editorContent` when `generate_prose.output_snapshot.generated_content` appears for the selected chapter. In `ChapterEditor`, remove the candidate section and show accept/reject buttons in the editor toolbar when a candidate exists.

- [ ] **Step 4: Verify frontend test**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: PASS.

---

### Task 2: Lock Editor While Generating

**Files:**
- Modify: `frontend/src/App.test.tsx`
- Modify: `frontend/src/components/ChapterEditor.tsx`

- [ ] **Step 1: Write failing component test**

Add a focused `ChapterEditor` test asserting that the `章节正文` textarea is disabled when `busy={true}`.

- [ ] **Step 2: Run failing test**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: FAIL because the textarea is not disabled while busy.

- [ ] **Step 3: Implement lock**

Set `disabled={busy}` on the chapter textarea.

- [ ] **Step 4: Verify frontend test**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: PASS.

---

### Task 3: Documentation And Verification

**Files:**
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/superpowers/plans/2026-07-16-inline-sse-editor-lock.md`

- [ ] **Step 1: Update module docs**

Change the SSE section to state that `generate_prose.output_snapshot.generated_content` is written into the center chapter textarea as the current candidate draft.

- [ ] **Step 2: Run verification**

Run:

```powershell
npm test -- --run
npm run build
python -m pytest -v
```

Expected:

- Frontend tests PASS.
- Frontend production build PASS.
- Backend tests PASS from the `backend` directory.

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add frontend docs
git commit -m "内联显示生成正文并锁定编辑"
git push
```

Expected: commit and push succeed.

---

## Self-Review

- Scope coverage: Inline SSE/prose display, deletion of generated-result block, and generation-time editor lock are covered.
- Scope control: No backend behavior, auto-generation flow, candidate acceptance API, or rewrite/edit-after-generation policy is changed.
- Type consistency: `liveGeneratedContent`, `chapter.generated_content`, and `editorContent` remain the only sources needed for visible chapter text.

## Implementation Result

- Existing persisted `chapter.generated_content` now appears directly in the `章节正文` textarea.
- `generate_prose.output_snapshot.generated_content` from SSE now updates the same textarea and is preserved across the immediate project refresh.
- The separate `生成结果` section was removed.
- Candidate `采纳` / `拒绝` actions now live in the editor toolbar when a candidate exists.
- The chapter textarea is disabled while `busy=true`, preventing edits during generation.

Focused verification:

- `npm test -- --run src/App.test.tsx`: 11 passed.

Final verification:

- `npm test -- --run` from `frontend`: 11 passed.
- `npm run build` from `frontend`: passed.
- `python -m pytest -v` from `backend`: 16 passed.
