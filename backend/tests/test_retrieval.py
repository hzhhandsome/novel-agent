from app.models.chapter import Chapter, ChapterStatus
from app.models.memory import StoryEvent, WorldRule
from app.services.chapter_service import generate_chapter_candidate
from app.services.vector_memory import VectorMemoryDocument, VectorMemoryHit, retrieve_hybrid_memory


class StaticVectorStore:
    backend_name = "static_vector"

    def __init__(self, hits: list[VectorMemoryHit] | None = None) -> None:
        self.hits = hits or []

    def search(self, project_id, query, documents, embedder, top_k):
        return self.hits[:top_k]


class UnusedEmbedder:
    def embed(self, texts):
        return [[1.0] for _ in texts]


def test_hybrid_retrieval_adds_keyword_only_hits_and_reranks():
    documents = [
        VectorMemoryDocument(
            source="foreshadowing_items",
            source_id="silver_needle",
            project_id=1,
            text="SILVER_NEEDLE_MARKER 银针藏在钟楼暗格里，仍未回收。",
            metadata={"status": "active"},
        ),
        VectorMemoryDocument(
            source="chapter_summaries",
            source_id="2",
            project_id=1,
            text="港口税务争执，与银针无关。",
            metadata={"chapter_number": 2},
        ),
    ]

    report = retrieve_hybrid_memory(
        project_id=1,
        query="银针 钟楼",
        documents=documents,
        store=StaticVectorStore(),
        embedder=UnusedEmbedder(),
        top_k=2,
    )

    assert report["strategy"] == "hybrid_reranked"
    assert report["backend"] == "hybrid_reranked:static_vector"
    assert report["hits"][0]["source_id"] == "silver_needle"
    assert report["hits"][0]["retrieval_source"] == "keyword"
    assert report["hits"][0]["ranker"] == "rule_rerank"
    assert "银针" in report["hits"][0]["matched_terms"]
    assert report["hits"][0]["score"] == report["hits"][0]["rerank_score"]


def test_hybrid_retrieval_marks_vector_keyword_overlap_as_hybrid():
    document = VectorMemoryDocument(
        source="story_events",
        source_id="event_1",
        project_id=1,
        text="RED_BOOK_MARKER 红封书在雨夜出现，关键同伴隐瞒来源。",
        metadata={"source_chapter_id": 3},
    )
    vector_hit = VectorMemoryHit(
        source=document.source,
        source_id=document.source_id,
        score=0.72,
        text=document.text,
        metadata=document.metadata,
    )

    report = retrieve_hybrid_memory(
        project_id=1,
        query="红封书 关键同伴",
        documents=[document],
        store=StaticVectorStore([vector_hit]),
        embedder=UnusedEmbedder(),
        top_k=1,
    )

    assert report["hits"][0]["retrieval_source"] == "hybrid"
    assert report["hits"][0]["vector_score"] == 0.72
    assert report["hits"][0]["keyword_score"] > 0
    assert "红封书" in report["hits"][0]["matched_terms"]


def test_load_context_retrieves_relevant_vector_memory_before_budget(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个失忆修书人在废城图书馆修补会改变现实的书"},
    ).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        project_id = project["id"]
        session.add(
            Chapter(
                project_id=project_id,
                number=6,
                title="更新的不相关旧章",
                status=ChapterStatus.accepted,
                content="远处港口发生了完全无关的争执。",
                summary="UNRELATED_MARKER 港口税务争执。" + ("无关内容。" * 400),
            )
        )
        session.add(
            Chapter(
                project_id=project_id,
                number=5,
                title="页码旧章",
                status=ChapterStatus.accepted,
                content="主角在废城图书馆发现手背页码会随修书变化。",
                summary="RELEVANT_PAGE_MARKER 废城图书馆的手背页码与修书会改变现实。" + ("相关内容。" * 60),
            )
        )
        session.flush()
        session.add(
            StoryEvent(
                project_id=project_id,
                source_chapter_id=None,
                title="手背页码显现",
                summary="RELEVANT_EVENT_MARKER 手背页码在废城图书馆出现。",
                characters="修书人",
                location="废城图书馆",
                consequence="主角意识到修书会改变现实",
            )
        )
        session.add(
            WorldRule(
                project_id=project_id,
                source_chapter_id=None,
                rule="RELEVANT_RULE_MARKER 修补不存在的书会改变现实，但会夺走一段记忆。",
                limitation="必须在废城图书馆内完成。",
                status="active",
            )
        )
        session.commit()

        first_chapter_id = project["chapters"][0]["id"]
        task = generate_chapter_candidate(session, first_chapter_id)
    finally:
        session_generator.close()

    load_context = next(step for step in task.steps if step.name == "load_context")
    package = load_context.output_snapshot["context_package"]
    retrieval = package["retrieval_results"]
    prompt_step = next(step for step in task.steps if step.name == "build_prompt_package")
    prompt_package = prompt_step.output_snapshot["prompt_package"]

    hit_text = " ".join(item["text"] for item in retrieval["hits"])
    assert retrieval["query"]
    assert retrieval["backend"] == "hybrid_reranked:local_vector"
    assert all(item["ranker"] == "rule_rerank" for item in retrieval["hits"])
    assert {item["retrieval_source"] for item in retrieval["hits"]} & {"vector", "keyword", "hybrid"}
    assert "RELEVANT_PAGE_MARKER" in hit_text
    assert "RELEVANT_EVENT_MARKER" in hit_text
    assert "RELEVANT_RULE_MARKER" in hit_text
    assert all(item["score"] > 0 for item in retrieval["hits"])
    assert "RELEVANT_PAGE_MARKER" in prompt_package
    assert "UNRELATED_MARKER" not in prompt_package
