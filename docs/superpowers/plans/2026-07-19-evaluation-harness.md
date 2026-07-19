# Evaluation Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic eval harness for summary fact retention and audit conflict detection.

**Architecture:** Keep eval outside the 11-node generation graph for the first phase. Add pure backend evaluation functions, built-in gold cases, and a runnable module command. Document the module so later prompt/model/RAG work can compare results against stable cases.

**Tech Stack:** Python dataclasses, Pytest, JSON CLI output.

---

### Task 1: Evaluation Core

**Files:**
- Create: `backend/app/services/evaluation.py`
- Test: `backend/tests/test_evaluation.py`

- [x] **Step 1: Write failing tests**

Create tests for summary retention and audit conflict recall.

- [x] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest backend/tests/test_evaluation.py -v
```

Expected: fails because `app.services.evaluation` does not exist.

- [x] **Step 3: Implement pure eval functions**

Add `ExpectedItem`, `evaluate_summary_fact_retention`, and `evaluate_audit_conflict_detection`.

- [x] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest backend/tests/test_evaluation.py -v
```

Expected: eval tests pass.

### Task 2: Built-In Gold Cases and Runner

**Files:**
- Create: `backend/app/evals/__init__.py`
- Create: `backend/app/evals/gold_cases.py`
- Create: `backend/app/evals/run.py`
- Test: `backend/tests/test_evaluation.py`

- [x] **Step 1: Add failing runner test**

Assert `run_builtin_evals()` returns summary and audit aggregate metrics.

- [x] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest backend/tests/test_evaluation.py -v
```

Expected: fails because the runner is missing.

- [x] **Step 3: Implement gold cases and runner**

Add small static gold cases and JSON-serializable aggregate output.

- [x] **Step 4: Run focused tests and CLI**

Run:

```powershell
python -m pytest backend/tests/test_evaluation.py -v
python -m app.evals.run
```

Expected: tests pass and CLI prints JSON.

### Task 3: Docs, Roadmap, Verification, Commit

**Files:**
- Create: `docs/modules/evaluation.md`
- Modify: `docs/modules/index.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-evaluation-harness.md`

- [x] **Step 1: Update docs**

Document eval scope, metrics, runner command, and current limitations.

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
git commit -m "实现基础评测框架"
git push
```

## Implementation Result

- Added deterministic summary fact retention eval.
- Added deterministic audit conflict detection eval.
- Added built-in gold cases and `python -m app.evals.run` JSON runner.
- Added evaluation module docs and roadmap status.

## Verification

- `python -m pytest -v` in `backend/`: 25 passed.
- `python -m app.evals.run` in `backend/`: produced 4 built-in cases, 4 passed.
- `npm test -- --run` in `frontend/`: 13 passed.
- `npm run build` in `frontend/`: passed.
