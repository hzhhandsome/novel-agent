from app.models.chapter import Chapter, ChapterStatus
from app.models.memory import StoryEvent, WorldRule
from app.services.chapter_service import generate_chapter_candidate


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
    assert retrieval["backend"] == "local_vector"
    assert "RELEVANT_PAGE_MARKER" in hit_text
    assert "RELEVANT_EVENT_MARKER" in hit_text
    assert "RELEVANT_RULE_MARKER" in hit_text
    assert all(item["score"] > 0 for item in retrieval["hits"])
    assert "RELEVANT_PAGE_MARKER" in prompt_package
    assert "UNRELATED_MARKER" not in prompt_package
