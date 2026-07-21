# Hybrid Retrieval And Rerank Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lightweight hybrid retrieval by combining vector recall, keyword recall, and deterministic rule reranking.

**Architecture:** Keep retrieval logic inside `backend/app/services/vector_memory.py`, call it from the existing `load_context` node, and preserve the existing `retrieval_results` shape with extra provenance fields.

**Tech Stack:** Python dataclasses, existing retrieval providers, pytest, React/TypeScript.

---

### Task 1: Backend Hybrid Retrieval

**Files:**
- Modify: `backend/tests/test_retrieval.py`
- Modify: `backend/app/services/vector_memory.py`
- Modify: `backend/app/agent/chapter_graph.py`

- [x] **Step 1: Write failing retrieval tests**

Add tests for keyword-only recall and vector+keyword hybrid provenance.

- [x] **Step 2: Run tests and confirm failure**

Run:

```powershell
cd backend
python -m pytest tests/test_retrieval.py -v
```

Expected: fails because `retrieve_hybrid_memory` does not exist and `load_context` still reports `local_vector`.

- [x] **Step 3: Implement hybrid retrieval**

Add `KeywordMemoryStore`, `retrieve_hybrid_memory`, merge/rerank helpers, and switch `load_context` to call hybrid retrieval.

- [x] **Step 4: Run retrieval tests**

Run:

```powershell
cd backend
python -m pytest tests/test_retrieval.py -v
```

Expected: retrieval tests pass.

### Task 2: RAG Eval Strategy Groups

**Files:**
- Modify: `backend/tests/test_evaluation.py`
- Modify: `backend/app/evals/run.py`
- Modify: `backend/app/evals/rag_cases.py`

- [x] **Step 1: Write failing Eval test**

Assert built-in Eval returns `rag.strategy_groups` with strategy names and average recall.

- [x] **Step 2: Implement strategy grouping**

Add strategy metadata to RAG cases and aggregate by strategy in `run_builtin_evals()`.

- [x] **Step 3: Run Eval tests**

Run:

```powershell
cd backend
python -m pytest tests/test_evaluation.py -v
python -m app.evals.run
```

Expected: report includes `rag.strategy_groups`.

### Task 3: Frontend Provenance Display

**Files:**
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend assertion**

Extend existing backstage snapshot test to expect `retrieval=hybrid` and `ranker=rule_rerank`.

- [x] **Step 2: Update formatter and types**

Show retrieval source, ranker, matched terms, and strategy group summaries.

- [x] **Step 3: Run frontend checks**

Run:

```powershell
cd frontend
npm test -- --run src/App.test.tsx -t "real generation step|runs built-in evals"
npm run build
```

Expected: tests and build pass.

### Task 4: Docs And Roadmap

**Files:**
- Modify: `docs/modules/retrieval.md`
- Modify: `docs/modules/evaluation.md`
- Modify: `docs/product/roadmap.md`

- [x] **Step 1: Update docs**

Record hybrid retrieval, keyword recall, rule rerank, and Eval strategy grouping.

- [x] **Step 2: Mark P0 status**

Mark `混合检索与 reranker` first stage completed and leave external reranker as future work.

- [x] **Step 3: Final verification**

Run:

```powershell
cd backend
python -m pytest tests/test_retrieval.py tests/test_evaluation.py -v
python -m app.evals.run
cd ..\frontend
npm test -- --run src/App.test.tsx -t "real generation step|runs built-in evals"
npm run build
```
