from __future__ import annotations

import math
import re
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import settings
from app.services.embeddings import EmbeddingProvider, get_embedding_provider


@dataclass(frozen=True)
class VectorMemoryDocument:
    source: str
    source_id: str
    project_id: int
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VectorMemoryHit:
    source: str
    source_id: str
    score: float
    text: str
    metadata: dict[str, Any]


class VectorMemoryStore(Protocol):
    backend_name: str

    def search(
        self,
        project_id: int,
        query: str,
        documents: list[VectorMemoryDocument],
        embedder: EmbeddingProvider,
        top_k: int,
    ) -> list[VectorMemoryHit]:
        raise NotImplementedError


class LocalVectorMemoryStore:
    backend_name = "local_vector"

    def search(
        self,
        project_id: int,
        query: str,
        documents: list[VectorMemoryDocument],
        embedder: EmbeddingProvider,
        top_k: int,
    ) -> list[VectorMemoryHit]:
        project_documents = [item for item in documents if item.project_id == project_id and item.text.strip()]
        if not query.strip() or not project_documents:
            return []

        vectors = embedder.embed([query] + [item.text for item in project_documents])
        query_vector = vectors[0]
        scored = [
            VectorMemoryHit(
                source=document.source,
                source_id=document.source_id,
                score=round(_cosine_similarity(query_vector, vector), 6),
                text=document.text,
                metadata=document.metadata,
            )
            for document, vector in zip(project_documents, vectors[1:], strict=True)
        ]
        return [item for item in sorted(scored, key=lambda hit: hit.score, reverse=True) if item.score > 0][:top_k]


class DisabledVectorMemoryStore:
    backend_name = "disabled"

    def search(
        self,
        project_id: int,
        query: str,
        documents: list[VectorMemoryDocument],
        embedder: EmbeddingProvider,
        top_k: int,
    ) -> list[VectorMemoryHit]:
        return []


class KeywordMemoryStore:
    backend_name = "keyword"

    def search(
        self,
        project_id: int,
        query: str,
        documents: list[VectorMemoryDocument],
        top_k: int,
    ) -> list[VectorMemoryHit]:
        terms = _query_terms(query)
        if not terms:
            return []

        hits: list[VectorMemoryHit] = []
        for document in documents:
            if document.project_id != project_id or not document.text.strip():
                continue
            searchable = _searchable_document_text(document)
            matched_terms = [term for term in terms if term in searchable]
            if not matched_terms:
                continue
            keyword_score = _keyword_score(matched_terms, terms)
            metadata = {
                **document.metadata,
                "matched_terms": matched_terms,
                "keyword_score": keyword_score,
                "retrieval_source": "keyword",
            }
            hits.append(
                VectorMemoryHit(
                    source=document.source,
                    source_id=document.source_id,
                    score=keyword_score,
                    text=document.text,
                    metadata=metadata,
                )
            )

        return sorted(
            hits,
            key=lambda hit: (hit.score, len(hit.metadata.get("matched_terms", [])), _source_priority(hit), hit.text),
            reverse=True,
        )[:top_k]


class QdrantVectorMemoryStore:
    backend_name = "qdrant"

    def __init__(self, url: str, collection: str, dimension: int) -> None:
        self.url = url
        self.collection = collection
        self.dimension = dimension
        self._client = None

    def search(
        self,
        project_id: int,
        query: str,
        documents: list[VectorMemoryDocument],
        embedder: EmbeddingProvider,
        top_k: int,
    ) -> list[VectorMemoryHit]:
        if not query.strip():
            return []

        self._ensure_collection()
        self._upsert_documents(documents, embedder)
        query_vector = embedder.embed([query])[0]
        try:
            results = self._client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                query_filter=self._project_filter(project_id),
                limit=top_k,
            )
        except Exception:
            return LocalVectorMemoryStore().search(project_id, query, documents, embedder, top_k)

        hits: list[VectorMemoryHit] = []
        for item in results:
            payload = item.payload or {}
            hits.append(
                VectorMemoryHit(
                    source=str(payload.get("source", "")),
                    source_id=str(payload.get("source_id", "")),
                    score=round(float(item.score), 6),
                    text=str(payload.get("text", "")),
                    metadata=dict(payload.get("metadata") or {}),
                )
            )
        return hits

    def _client_instance(self):
        if self._client is None:
            from qdrant_client import QdrantClient

            self._client = QdrantClient(url=self.url)
        return self._client

    def _ensure_collection(self) -> None:
        client = self._client_instance()
        from qdrant_client.models import Distance, VectorParams

        if client.collection_exists(self.collection):
            return
        client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
        )

    def _upsert_documents(self, documents: list[VectorMemoryDocument], embedder: EmbeddingProvider) -> None:
        clean_documents = [item for item in documents if item.text.strip()]
        if not clean_documents:
            return

        from qdrant_client.models import PointStruct

        vectors = embedder.embed([item.text for item in clean_documents])
        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document.project_id}:{document.source}:{document.source_id}")),
                vector=vector,
                payload={
                    "project_id": document.project_id,
                    "source": document.source,
                    "source_id": document.source_id,
                    "text": document.text,
                    "metadata": document.metadata,
                },
            )
            for document, vector in zip(clean_documents, vectors, strict=True)
        ]
        self._client_instance().upsert(collection_name=self.collection, points=points)

    @staticmethod
    def _project_filter(project_id: int):
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        return Filter(must=[FieldCondition(key="project_id", match=MatchValue(value=project_id))])


def get_vector_memory_store() -> VectorMemoryStore:
    if settings.retrieval_backend == "disabled":
        return DisabledVectorMemoryStore()
    if settings.retrieval_backend == "qdrant":
        return QdrantVectorMemoryStore(
            settings.qdrant_url,
            settings.qdrant_collection,
            settings.embedding_dimension,
        )
    return LocalVectorMemoryStore()


def retrieve_vector_memory(
    project_id: int,
    query: str,
    documents: list[VectorMemoryDocument],
    store: VectorMemoryStore | None = None,
    embedder: EmbeddingProvider | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    vector_store = store or get_vector_memory_store()
    embedding_provider = embedder or get_embedding_provider()
    hits = vector_store.search(project_id, query, documents, embedding_provider, top_k or settings.retrieval_top_k)
    return {
        "backend": vector_store.backend_name,
        "query": query,
        "hits": [
            {
                "source": item.source,
                "source_id": item.source_id,
                "score": item.score,
                "text": item.text,
                "metadata": item.metadata,
            }
            for item in hits
        ],
    }


def retrieve_hybrid_memory(
    project_id: int,
    query: str,
    documents: list[VectorMemoryDocument],
    store: VectorMemoryStore | None = None,
    embedder: EmbeddingProvider | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    vector_store = store or get_vector_memory_store()
    limit = top_k or settings.retrieval_top_k
    if vector_store.backend_name == "disabled":
        return retrieve_vector_memory(project_id, query, documents, vector_store, embedder, limit)

    embedding_provider = embedder or get_embedding_provider()
    vector_hits = vector_store.search(project_id, query, documents, embedding_provider, limit)
    keyword_hits = KeywordMemoryStore().search(project_id, query, documents, max(limit * 2, limit))
    hits = _merge_and_rerank_hits(vector_hits, keyword_hits, limit)
    return {
        "backend": f"hybrid_reranked:{vector_store.backend_name}",
        "strategy": "hybrid_reranked",
        "query": query,
        "source_counts": {
            "vector": sum(1 for item in hits if item.metadata.get("retrieval_source") == "vector"),
            "keyword": sum(1 for item in hits if item.metadata.get("retrieval_source") == "keyword"),
            "hybrid": sum(1 for item in hits if item.metadata.get("retrieval_source") == "hybrid"),
        },
        "hits": [_hit_payload(item) for item in hits],
    }


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(item * item for item in left))
    right_norm = math.sqrt(sum(item * item for item in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _merge_and_rerank_hits(
    vector_hits: list[VectorMemoryHit],
    keyword_hits: list[VectorMemoryHit],
    top_k: int,
) -> list[VectorMemoryHit]:
    merged: dict[str, dict[str, Any]] = {}
    for hit in vector_hits:
        identity = _hit_identity(hit)
        merged[identity] = {
            "source": hit.source,
            "source_id": hit.source_id,
            "text": hit.text,
            "metadata": dict(hit.metadata),
            "vector_score": hit.score,
            "keyword_score": 0.0,
            "matched_terms": [],
        }

    for hit in keyword_hits:
        identity = _hit_identity(hit)
        record = merged.setdefault(
            identity,
            {
                "source": hit.source,
                "source_id": hit.source_id,
                "text": hit.text,
                "metadata": dict(hit.metadata),
                "vector_score": 0.0,
                "keyword_score": 0.0,
                "matched_terms": [],
            },
        )
        record["metadata"] = {**record["metadata"], **hit.metadata}
        record["keyword_score"] = max(float(record["keyword_score"]), hit.score)
        record["matched_terms"] = sorted(set(record["matched_terms"]) | set(hit.metadata.get("matched_terms", [])))

    reranked: list[VectorMemoryHit] = []
    for record in merged.values():
        vector_score = float(record["vector_score"])
        keyword_score = float(record["keyword_score"])
        retrieval_source = "hybrid" if vector_score and keyword_score else "vector" if vector_score else "keyword"
        metadata = {
            **record["metadata"],
            "retrieval_source": retrieval_source,
            "ranker": "rule_rerank",
            "vector_score": round(vector_score, 6),
            "keyword_score": round(keyword_score, 6),
            "matched_terms": record["matched_terms"],
        }
        rerank_score = _rerank_score(
            source=str(record["source"]),
            metadata=metadata,
            vector_score=vector_score,
            keyword_score=keyword_score,
        )
        metadata["rerank_score"] = rerank_score
        reranked.append(
            VectorMemoryHit(
                source=str(record["source"]),
                source_id=str(record["source_id"]),
                score=rerank_score,
                text=str(record["text"]),
                metadata=metadata,
            )
        )

    return sorted(reranked, key=lambda hit: (hit.score, _source_priority(hit), hit.text), reverse=True)[:top_k]


def _hit_payload(hit: VectorMemoryHit) -> dict[str, Any]:
    return {
        "source": hit.source,
        "source_id": hit.source_id,
        "score": hit.score,
        "text": hit.text,
        "metadata": hit.metadata,
        "retrieval_source": hit.metadata.get("retrieval_source", ""),
        "ranker": hit.metadata.get("ranker", ""),
        "matched_terms": hit.metadata.get("matched_terms", []),
        "vector_score": hit.metadata.get("vector_score", 0.0),
        "keyword_score": hit.metadata.get("keyword_score", 0.0),
        "rerank_score": hit.metadata.get("rerank_score", hit.score),
    }


def _hit_identity(hit: VectorMemoryHit) -> str:
    return f"{hit.source}:{hit.source_id}"


def _query_terms(query: str) -> list[str]:
    normalized = query.strip()
    if not normalized:
        return []

    terms: set[str] = set()
    for token in re.findall(r"[A-Za-z0-9_]{2,}", normalized):
        terms.add(token)
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", normalized):
        terms.add(phrase)
        max_len = min(6, len(phrase))
        for size in range(2, max_len + 1):
            for index in range(0, len(phrase) - size + 1):
                terms.add(phrase[index : index + size])

    stop_terms = {"一个", "这个", "那个", "是否", "当前", "小说", "章节", "故事"}
    return sorted(term for term in terms if term not in stop_terms)


def _searchable_document_text(document: VectorMemoryDocument) -> str:
    metadata_text = " ".join(str(value) for value in document.metadata.values() if value is not None)
    return f"{document.text} {metadata_text}"


def _keyword_score(matched_terms: list[str], all_terms: list[str]) -> float:
    if not all_terms:
        return 0.0
    exact_weight = sum(min(len(term), 6) for term in matched_terms)
    possible_weight = max(1, sum(min(len(term), 6) for term in all_terms))
    return round(min(1.0, exact_weight / possible_weight * 3), 6)


def _rerank_score(source: str, metadata: dict[str, Any], vector_score: float, keyword_score: float) -> float:
    score = vector_score * 0.7 + keyword_score * 0.55
    score += _metadata_boost(source, metadata)
    return round(min(1.0, score), 6)


def _metadata_boost(source: str, metadata: dict[str, Any]) -> float:
    boost = 0.0
    if source == "foreshadowing_items" and str(metadata.get("status", "")).lower() in {"active", "open", "advanced"}:
        boost += 0.08
    if source == "characters":
        boost += 0.05
    chapter_number = metadata.get("chapter_number") or metadata.get("source_chapter_id")
    try:
        boost += min(float(chapter_number) / 1000, 0.04)
    except (TypeError, ValueError):
        pass
    return boost


def _source_priority(hit: VectorMemoryHit) -> int:
    order = {
        "foreshadowing_items": 5,
        "characters": 4,
        "story_events": 3,
        "world_rules": 2,
        "chapter_summaries": 1,
    }
    return order.get(hit.source, 0)
