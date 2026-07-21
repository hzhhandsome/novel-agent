# Hybrid Retrieval And Rerank Design

## Goal

Add a lightweight hybrid retrieval path for chapter context loading, combining existing vector retrieval with keyword recall and deterministic rule-based reranking.

## Scope

- Keep the existing vector retrieval backends: `local`, `qdrant`, and `disabled`.
- Add keyword recall over the same formal-memory documents used by vector retrieval.
- Merge vector and keyword hits by `source/source_id`.
- Rerank merged hits with deterministic rules.
- Include per-hit provenance so the Agent backstage can show whether a hit came from `vector`, `keyword`, or `hybrid`, and whether it was reranked.
- Extend built-in RAG Eval output with strategy grouping so reports can compare retrieval strategies.

Out of scope:

- Do not add an external reranker model.
- Do not add new database tables.
- Do not change Qdrant payload shape in a breaking way.
- Do not index candidate chapters or unaccepted content.
- Do not change the 11-node LangGraph flow.

## Architecture

`backend/app/services/vector_memory.py` remains the retrieval service boundary. It will gain:

- `KeywordMemoryStore`: scores documents by query term matches.
- `retrieve_hybrid_memory(...)`: calls the configured vector store, runs keyword recall, merges hits, and applies rule reranking.

`backend/app/agent/chapter_graph.py` will call `retrieve_hybrid_memory` in `load_context`. The output shape stays compatible with existing `retrieval_results`, but each hit also includes:

- `retrieval_source`: `vector`, `keyword`, or `hybrid`
- `ranker`: `rule_rerank`
- `matched_terms`
- `vector_score`
- `keyword_score`
- `rerank_score`

`frontend/src/components/AgentWorkspace.tsx` will display these provenance fields in the existing RAG recall text.

## Rerank Rules

The first-stage deterministic reranker combines:

- Vector score from the configured vector backend.
- Keyword score from query/document term overlap.
- Small source boosts for active foreshadowing, characters, and recent chapter/event metadata.

The final score is saved as `rerank_score` and used as the returned hit `score`.

## Error Handling

If the configured retrieval backend is `disabled`, hybrid retrieval returns no hits, preserving the meaning of disabled retrieval. If Qdrant fails, the existing Qdrant fallback to local vector retrieval remains in effect.

## Testing

- Unit test keyword-only hits are recalled and marked as `keyword`.
- Unit test overlap between vector and keyword recall is marked as `hybrid`.
- Integration test `load_context` returns hybrid backend provenance and still feeds relevant memory into prompt budget.
- Eval test ensures RAG report exposes strategy groups.
- Frontend test ensures backstage RAG display includes retrieval provenance.
