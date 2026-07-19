# Vector RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add vector RAG with Docker Qdrant and local free embeddings, then feed recalled memory into context budgeting.

**Architecture:** Add small embedding and vector-memory service modules. `load_context` remains the LangGraph entry node and calls the vector retrieval layer before `_build_context_budget`. Docker uses Qdrant plus `sentence-transformers`; tests use deterministic local embeddings and in-process vector ranking.

**Tech Stack:** FastAPI, SQLAlchemy, LangGraph, Qdrant, sentence-transformers, React, TypeScript, Pytest, Vitest.

---

### Task 1: Backend Vector Retrieval

**Files:**
- Create: `backend/app/services/embeddings.py`
- Create: `backend/app/services/vector_memory.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/agent/chapter_graph.py`
- Test: `backend/tests/test_retrieval.py`

- [x] **Step 1: Write failing backend test**

`backend/tests/test_retrieval.py` asserts vector retrieval metadata exists, relevant formal memory is recalled, and unrelated old context stays out of the prompt.

- [x] **Step 2: Run test to verify failure**

Run:

```powershell
python -m pytest backend/tests/test_retrieval.py -v
```

Expected: fails because `retrieval_results` is missing.

- [x] **Step 3: Implement embedding and vector memory services**

Add `HashEmbeddingProvider`, lazy `SentenceTransformerEmbeddingProvider`, `LocalVectorMemoryStore`, and lazy `QdrantVectorMemoryStore`.

- [x] **Step 4: Connect retrieval in `load_context`**

Build formal memory documents, retrieve top K, sort candidates by hit order, expose `retrieval_results`, and let `context_budget` decide final prompt inclusion.

- [x] **Step 5: Run focused backend tests**

Run:

```powershell
python -m pytest backend/tests/test_retrieval.py backend/tests/test_context_budget.py backend/tests/test_structured_memory.py backend/tests/test_chapter_generation.py -v
```

Expected: all selected tests pass.

### Task 2: Docker Runtime Wiring

**Files:**
- Modify: `docker-compose.yml`
- Modify: `backend/pyproject.toml`
- Modify: `README.md`
- Modify: `scripts/start-dev.ps1`

- [x] **Step 1: Add Qdrant Docker service**

Add `qdrant` service on ports `6333` and `6334`, with a named volume.

- [x] **Step 2: Add runtime dependencies**

Add `qdrant-client` and `sentence-transformers` to backend dependencies.

- [x] **Step 3: Configure Docker backend env**

Set:

```yaml
NOVEL_AGENT_RETRIEVAL_BACKEND: qdrant
NOVEL_AGENT_QDRANT_URL: http://qdrant:6333
NOVEL_AGENT_EMBEDDING_PROVIDER: sentence_transformers
NOVEL_AGENT_EMBEDDING_MODEL: BAAI/bge-small-zh-v1.5
NOVEL_AGENT_EMBEDDING_DIMENSION: 384
```

- [x] **Step 4: Update startup docs/scripts**

Document Qdrant port and update local script to start `postgres` and `qdrant`.

### Task 3: Frontend Retrieval Display

**Files:**
- Modify: `frontend/src/components/AgentWorkspace.tsx`
- Test: `frontend/src/App.test.tsx`

- [x] **Step 1: Write failing frontend test**

Extend the backstage context fixture with `retrieval_results` and assert the context tab shows backend/query/hit text.

- [x] **Step 2: Run test to verify failure**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: fails before the UI displays retrieval data.

- [x] **Step 3: Implement display**

Add a compact formatter and a `["RAG 召回", ...]` context card.

- [x] **Step 4: Run focused frontend tests**

Run:

```powershell
npm test -- --run src/App.test.tsx
```

Expected: all app tests pass.

### Task 4: Docs, Verification, Commit

**Files:**
- Create: `docs/modules/retrieval.md`
- Modify: `docs/modules/generation-flow.md`
- Modify: `docs/modules/memory-system.md`
- Modify: `docs/modules/index.md`
- Modify: `docs/product/roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-19-vector-rag.md`

- [x] **Step 1: Update docs**

Document Qdrant, local embedding, retrieval timing, formal-memory-only indexing, fallback behavior, and test commands.

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
git commit -m "实现向量检索召回"
git push
```

## Implementation Result

- Added local hash embedding and lazy sentence-transformers embedding providers.
- Added local vector retrieval and lazy Qdrant vector retrieval.
- Connected `load_context` to vector retrieval before context budgeting.
- Added Docker Qdrant service and runtime embedding configuration.
- Displayed RAG backend, query, and hits in the Agent backstage context tab.
- Added retrieval module documentation and updated roadmap/module docs.

## Verification

- `python -m pytest -v` in `backend/`: 22 passed.
- `npm test -- --run` in `frontend/`: 13 passed.
- `npm run build` in `frontend/`: passed.
- `docker compose config`: passed.
