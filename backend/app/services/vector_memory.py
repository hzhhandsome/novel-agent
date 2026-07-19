from __future__ import annotations

import math
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


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(item * item for item in left))
    right_norm = math.sqrt(sum(item * item for item in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
