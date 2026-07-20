# LLM-as-judge Eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight offline LLM-as-judge Eval report to the existing built-in Eval flow.

**Architecture:** Add fixed judge cases, a provider-level judge method, pure result aggregation, and frontend display in the existing Eval panel. Do not modify the 11-node chapter generation graph.

**Tech Stack:** FastAPI, Python dataclasses, existing provider abstraction, pytest, React/TypeScript.

---

### Task 1: Backend Judge Evaluation

**Files:**
- Modify: `backend/tests/test_evaluation.py`
- Create: `backend/app/evals/judge_cases.py`
- Modify: `backend/app/services/evaluation.py`
- Modify: `backend/app/services/model_provider.py`
- Modify: `backend/app/evals/run.py`
- Modify: `backend/app/services/prompt_versions.py`

- [x] **Step 1: Write failing backend tests**

Add tests asserting:

```python
def test_llm_judge_eval_aggregates_scores():
    from app.services.evaluation import evaluate_llm_judge_result

    result = evaluate_llm_judge_result(
        case_id="character_drift",
        case_name="角色动机偏离",
        scores={"consistency": 0.8, "character": 0.6, "foreshadowing": 1.0, "style": 0.8},
        blocking_findings=["主角突然放弃核心目标"],
        reason="人物动机偏离。",
        threshold=0.75,
    )

    assert result["metric"] == "llm_judge"
    assert result["average_score"] == 0.8
    assert result["passed"] is False
    assert result["blocking_findings"] == ["主角突然放弃核心目标"]
```

Extend `test_builtin_eval_runner_returns_aggregate_metrics` to assert `report["judge"]["case_count"] >= 1` and `report["judge"]["average_score"] > 0`.

- [x] **Step 2: Run tests and confirm failure**

Run:

```powershell
cd backend
python -m pytest tests/test_evaluation.py -v
```

Expected: fails because `evaluate_llm_judge_result` and `judge` report do not exist.

- [x] **Step 3: Implement backend judge**

Create fixed judge cases, add `JudgeEvalResult`, `ModelProvider.judge_eval_case`, mock/DeepSeek implementations, prompt version `llm_judge_eval`, and aggregate `judge` in `run_builtin_evals()`.

- [x] **Step 4: Run backend tests**

Run:

```powershell
cd backend
python -m pytest tests/test_evaluation.py tests/test_model_provider.py -v
python -m app.evals.run
```

Expected: tests pass and CLI JSON includes `judge`.

### Task 2: Frontend Eval Display

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/AgentWorkspace.tsx`

- [x] **Step 1: Extend frontend types and UI**

Add optional `judge` metric fields to `BuiltinEvalReport`. In the Eval card, show:

- `Judge 语义分`
- `Judge 通过数`
- failed case summary from `judge.cases`

- [x] **Step 2: Run frontend verification**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "real generation step"
npm run build
```

Expected: targeted test and build pass.

### Task 3: Docs and Roadmap

**Files:**
- Modify: `docs/modules/evaluation.md`
- Modify: `docs/modules/model-provider.md`
- Modify: `docs/product/roadmap.md`

- [x] **Step 1: Update module docs**

Record that built-in Eval now includes lightweight LLM-as-judge and that provider exposes a dedicated judge method.

- [x] **Step 2: Update roadmap status**

Mark `LLM-as-judge 语义评测` as first-stage completed in P0.

- [x] **Step 3: Final verification**

Run:

```powershell
cd backend
python -m pytest tests/test_evaluation.py tests/test_model_provider.py -v
python -m app.evals.run
cd ..\frontend
npm run build
```

Expected: all commands exit 0.
