# Training Data Prep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-stage JSONL training data export from accepted generation runs.

**Architecture:** Add a focused backend service that transforms `GenerationRun` records into provider-neutral examples. Add a CLI entry point that writes JSONL from the configured database. Document boundaries in a new module doc.

**Tech Stack:** SQLAlchemy, JSONL, Pytest.

---

### Task 1: Export Service

**Files:**
- Create: `backend/app/services/training_data.py`
- Test: `backend/tests/test_training_data.py`

- [x] **Step 1: Write failing export tests**
- [x] **Step 2: Implement example generation and JSONL serialization**
- [x] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest backend/tests/test_training_data.py -v
```

### Task 2: CLI Entry

**Files:**
- Create: `backend/app/training_data/__init__.py`
- Create: `backend/app/training_data/export.py`
- Test: `backend/tests/test_training_data.py`

- [x] **Step 1: Write failing CLI smoke test**
- [x] **Step 2: Implement CLI wrapper**
- [x] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest backend/tests/test_training_data.py -v
```

### Task 3: Docs, Verification, Commit

**Files:**
- Create: `docs/modules/training-data.md`
- Modify: `docs/modules/index.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-training-data-prep.md`

- [x] **Step 1: Update docs**
- [x] **Step 2: Run verification**

Run:

```powershell
python -m pytest -v
npm test -- --run
npm run build
```

Result:

- `backend`: 40 passed.
- `frontend`: 18 passed.
- `frontend build`: passed.

- [ ] **Step 3: Commit and push**

```powershell
git add .
git commit -m "实现微调数据准备"
git push
```
