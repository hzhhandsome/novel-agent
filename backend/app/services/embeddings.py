from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

from app.core.config import settings


class EmbeddingProvider(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class HashEmbeddingProvider:
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [_normalize(_hash_vector(text, self.dimension)) for text in texts]


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str, dimension: int = 384) -> None:
        self.model_name = model_name
        self.dimension = dimension
        self._model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        vectors = model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model


def get_embedding_provider() -> EmbeddingProvider:
    if settings.embedding_provider == "sentence_transformers":
        return SentenceTransformerEmbeddingProvider(settings.embedding_model, settings.embedding_dimension)
    return HashEmbeddingProvider(settings.embedding_dimension)


def _hash_vector(text: str, dimension: int) -> list[float]:
    vector = [0.0] * dimension
    for token in _tokenize_for_hash_embedding(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        vector[index] += 1.0
    return vector


def _tokenize_for_hash_embedding(text: str) -> list[str]:
    tokens: list[str] = []
    for ascii_word in re.findall(r"[A-Za-z0-9_]{2,}", text.lower()):
        tokens.append(ascii_word)

    for segment in re.findall(r"[\u4e00-\u9fff]{2,}", text):
        length = len(segment)
        for size in (2, 3, 4):
            if length < size:
                continue
            tokens.extend(segment[index : index + size] for index in range(0, length - size + 1))
    return tokens


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(item * item for item in vector))
    if magnitude == 0:
        return vector
    return [item / magnitude for item in vector]
