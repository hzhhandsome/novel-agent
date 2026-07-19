from app.models.chapter import Chapter, ChapterStatus
from app.models.memory import StoryEvent
from app.services.chapter_service import generate_chapter_candidate


def test_load_context_applies_budget_and_omits_old_summaries(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"},
    ).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        project_id = project["id"]
        for number in range(4, 18):
            old_marker = f"OLD_SUMMARY_{number}"
            session.add(
                Chapter(
                    project_id=project_id,
                    number=number,
                    title=f"历史章节 {number}",
                    status=ChapterStatus.accepted,
                    content=f"历史正文 {number}",
                    summary=f"{old_marker} " + ("旧摘要内容。" * 80),
                )
            )
        session.flush()
        for number in range(1, 10):
            session.add(
                StoryEvent(
                    project_id=project_id,
                    source_chapter_id=None,
                    title=f"历史事件 {number}",
                    summary=f"OLD_EVENT_{number} " + ("旧事件内容。" * 80),
                    characters="主角",
                    location="图书馆",
                    consequence="历史后果",
                )
            )
        session.commit()

        first_chapter_id = project["chapters"][0]["id"]
        task = generate_chapter_candidate(session, first_chapter_id)
    finally:
        session_generator.close()

    load_context = next(step for step in task.steps if step.name == "load_context")
    package = load_context.output_snapshot["context_package"]
    budget = package["context_budget"]
    prompt_step = next(step for step in task.steps if step.name == "build_prompt_package")
    prompt_package = prompt_step.output_snapshot["prompt_package"]

    assert budget["total_budget"] == 6000
    assert budget["used"] <= budget["total_budget"]
    assert budget["sections"]
    assert budget["omitted"]["chapter_summaries"]
    assert budget["omitted"]["story_events"]
    assert len(package["chapter_summaries"]) < 14
    assert "OLD_SUMMARY_4" in " ".join(budget["omitted"]["chapter_summaries"])
    assert "OLD_SUMMARY_4" not in prompt_package
    assert "OLD_EVENT_1" in " ".join(budget["omitted"]["story_events"])
    assert "OLD_EVENT_1" not in prompt_package
