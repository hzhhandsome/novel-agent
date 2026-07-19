# Foreshadowing Memory Backfill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make accepted chapter foreshadowing decisions reliably appear in the formal foreshadowing memory list, including existing accepted chapters whose decisions were already stored only in generation task snapshots.

**Architecture:** Keep candidate generation and formal memory separated. Acceptance remains the only write boundary for formal memory, and a small idempotent backfill service replays accepted chapter task snapshots into `ForeshadowingItem`.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, existing LangGraph generation task snapshots.

---

## File Structure

- Modify: `backend/app/services/chapter_service.py`
  - Normalize foreshadowing decision items returned as strings or JSON objects.
  - Upsert foreshadowing records by project/content so later chapters can advance or recover existing伏笔.
  - Add an idempotent project backfill helper that replays accepted chapter snapshots.
- Modify: `backend/app/api/routes/projects.py`
  - Add a narrow maintenance endpoint for backfilling formal memory from accepted chapter task snapshots.
- Modify: `backend/tests/test_structured_memory.py`
  - Add regression tests for dict-shaped foreshadowing items and project backfill.
- Modify: `docs/modules/memory-system.md`
  - Document that伏笔 is part of formal structured memory and how backfill works.

### Task 1: Regression Tests

- [x] **Step 1: Add tests**

Add tests in `backend/tests/test_structured_memory.py` that assert:

```python
def test_accepting_chapter_normalizes_dict_foreshadowing_items(client_with_db):
    ...
```

The generated task step output should contain `{"new": [{"content": "门牌数字反复减少", "reason": "用于后续回收"}]}` and the project response should contain a formal `foreshadowing_items` entry with content `门牌数字反复减少`.

Add:

```python
def test_backfill_project_foreshadowing_replays_accepted_task_snapshots(client_with_db):
    ...
```

The test should remove formal `ForeshadowingItem` rows after accepting a chapter, call `POST /api/projects/{project_id}/memory/backfill`, and assert the row is restored exactly once.

- [x] **Step 2: Run tests and verify they fail**

Run:

```powershell
cd backend
python -m pytest tests/test_structured_memory.py -v
```

Expected: new tests fail because dict items are stringified poorly or no backfill endpoint exists.

### Task 2: Foreshadowing Commit and Backfill

- [x] **Step 1: Implement normalization and upsert**

In `backend/app/services/chapter_service.py`, update `_string_items` or add a helper so dict items use `content`, `伏笔`, `foreshadowing`, `description`, or joined scalar values. Update `_commit_foreshadowing_items` to find existing rows by `project_id` and `content`, preserving original `source_chapter_id` when advancing/recovering.

- [x] **Step 2: Add backfill helper**

Add:

```python
def backfill_project_foreshadowing_memory(session: Session, project_id: int) -> dict:
    ...
```

It should iterate accepted chapters for the project, find each latest `chapter_generation` task, call `_commit_foreshadowing_items`, commit once, and return counts.

- [x] **Step 3: Add route**

In `backend/app/api/routes/projects.py`, expose:

```python
@router.post("/{project_id}/memory/backfill")
def backfill_project_memory(...):
    ...
```

Return the helper result.

- [x] **Step 4: Run structured memory tests**

Run:

```powershell
cd backend
python -m pytest tests/test_structured_memory.py -v
```

Expected: all tests pass.

### Task 3: Docs and Verification

- [x] **Step 1: Update memory module doc**

Document:

- `ForeshadowingItem` is formal structured memory.
- Formal伏笔 is written only on acceptance or explicit maintenance backfill.
- Candidate `judge_foreshadowing` output alone is not enough for right-side module display.
- Character cards should be concise in the module panel; full raw model output belongs in Agent后台.

- [x] **Step 2: Run related backend tests**

Run:

```powershell
cd backend
python -m pytest tests/test_structured_memory.py tests/test_chapter_generation.py tests/test_auto_generation.py -v
```

Expected: all tests pass.
