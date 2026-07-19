# Vector RAG Design

## Goal

Add a P0 vector retrieval layer so chapter generation can recall relevant old information by character, foreshadowing, location, and semantic similarity before building the final prompt.

## Scope

This design covers first-stage vector RAG:

- Add Qdrant to Docker Compose as the vector database.
- Add a local free embedding provider based on `sentence-transformers`, defaulting to `BAAI/bge-small-zh-v1.5` for Docker/runtime.
- Keep tests lightweight with a deterministic local hash embedding provider and in-process vector ranking.
- Index only formal memory: accepted chapter summaries, story events, world rules, character period cards, and foreshadowing items.
- Run retrieval from `load_context`, expose `context_package.retrieval_results`, and feed retrieved items into the context budget.
- Show retrieval hits in the Agent backstage context tab.

This does not add user-managed embedding jobs, vector reranking, recall@k eval, or a separate vector administration UI.

## Architecture

### Embedding

`backend/app/services/embeddings.py` owns embedding providers:

- `HashEmbeddingProvider`: deterministic local provider for tests and offline fallback.
- `SentenceTransformerEmbeddingProvider`: lazy-loads `sentence-transformers` and the configured model.

Configuration:

- `NOVEL_AGENT_EMBEDDING_PROVIDER=hash|sentence_transformers`
- `NOVEL_AGENT_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5`
- `NOVEL_AGENT_EMBEDDING_DIMENSION=384`

### Vector Store

`backend/app/services/vector_memory.py` owns retrieval storage:

- `LocalVectorMemoryStore`: builds vectors from current DB candidates in-process, used by tests and local fallback.
- `QdrantVectorMemoryStore`: upserts formal memory into Qdrant and searches by `project_id`.

Configuration:

- `NOVEL_AGENT_RETRIEVAL_BACKEND=local|qdrant|disabled`
- `NOVEL_AGENT_QDRANT_URL=http://qdrant:6333`
- `NOVEL_AGENT_QDRANT_COLLECTION=novel_agent_memory`
- `NOVEL_AGENT_RETRIEVAL_TOP_K=8`

### Data Flow

1. `load_context` reads formal DB context.
2. It builds vector memory documents from chapter summaries, story events, world rules, character cards, and foreshadowing.
3. It builds the retrieval query from current chapter title, project positioning, worldview, main plot, character periods, and unapplied inspirations.
4. It upserts documents to Qdrant when the backend is `qdrant`; otherwise it ranks locally.
5. It searches top K by vector similarity.
6. It sorts context candidates so retrieved items are considered first by the context budget.
7. It writes `context_package.retrieval_results` for debugging.

### Write Boundary

Only formal memory should be indexed. Candidate text is not vectorized before acceptance. Full automatic generation still calls the normal acceptance path, so accepted chapters become indexable formal memory on the next generation.

## Context Package Shape

```json
{
  "retrieval_results": {
    "backend": "qdrant",
    "query": "第 3 章 废城图书馆 修书 记忆代价",
    "hits": [
      {
        "source": "story_events",
        "source_id": "7",
        "score": 0.82,
        "text": "第 2 章：主角发现手背页码",
        "metadata": {"source_chapter_id": 2}
      }
    ]
  }
}
```

`context_budget` remains the authority for what actually entered the prompt.

## Tests

Backend tests:

- Use local vector backend and hash embeddings.
- Build a project with relevant old memory and unrelated old memory.
- Generate a chapter.
- Assert `retrieval_results.backend == "local_vector"`.
- Assert relevant summary/event/rule appear in retrieval hits and prompt.
- Assert unrelated old marker is excluded from prompt.

Frontend tests:

- Agent context tab displays retrieval backend, query, and hit text when present.

