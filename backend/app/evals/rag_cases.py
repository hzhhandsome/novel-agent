from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.evaluation import ExpectedRetrievedDocument


@dataclass(frozen=True)
class RagRetrievalCase:
    name: str
    retrieval_report: dict[str, Any]
    expected_documents: list[ExpectedRetrievedDocument]
    top_k: int = 5
    threshold: float = 0.8


RAG_RETRIEVAL_CASES = [
    RagRetrievalCase(
        name="foreshadowing_memory_recall",
        retrieval_report={
            "backend": "gold_case",
            "strategy": "hybrid_reranked",
            "query": "红封书来源和关键同伴隐瞒",
            "hits": [
                {
                    "source": "foreshadowing",
                    "source_id": "red_page_note",
                    "score": 0.93,
                    "text": "红封书页留下未知批注，关键同伴隐瞒曾经修书的经历。",
                    "metadata": {"chapter": 2},
                },
                {
                    "source": "chapter_summary",
                    "source_id": "1",
                    "score": 0.72,
                    "text": "主角确认修书会改变现实。",
                    "metadata": {"chapter": 1},
                },
            ],
        },
        expected_documents=[
            ExpectedRetrievedDocument(source="foreshadowing", source_id="red_page_note", label="红封书页未知批注"),
        ],
        top_k=3,
        threshold=1.0,
    ),
]
