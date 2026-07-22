import re

from app.models.chapter import Chapter, ChapterStatus
from app.models.memory import StoryEvent
from app.services.chapter_service import generate_chapter_candidate
from app.services.provider_factory import update_runtime_model_config


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

    assert budget["model_max_tokens"] == 4096
    assert budget["reserved_output_tokens"] > 0
    assert budget["fixed_prompt_reserve_tokens"] > 0
    assert budget["context_budget_tokens"] == budget["total_budget"]
    assert budget["estimated_tokens"] == budget["used"]
    assert budget["estimated_chars"] > 0
    assert budget["counter_name"]
    assert budget["used"] <= budget["total_budget"]
    assert budget["sections"]
    assert all("used_tokens" in section and "used_chars" in section for section in budget["sections"])
    assert budget["omitted"]["chapter_summaries"]
    assert budget["omitted"]["story_events"]
    assert len(package["chapter_summaries"]) < 14
    omitted_summaries = " ".join(budget["omitted"]["chapter_summaries"])
    omitted_events = " ".join(budget["omitted"]["story_events"])
    omitted_summary_markers = re.findall(r"OLD_SUMMARY_\d+", omitted_summaries)
    omitted_event_markers = re.findall(r"OLD_EVENT_\d+", omitted_events)
    assert omitted_summary_markers
    assert omitted_event_markers
    assert all(marker not in prompt_package for marker in omitted_summary_markers)
    assert all(marker not in prompt_package for marker in omitted_event_markers)


def test_context_budget_uses_task_model_max_tokens(client_with_db):
    update_runtime_model_config(provider="mock", max_tokens=2048, api_key="", routes={"generation": None, "audit": None, "summary": None})
    project = client_with_db.post("/api/projects", json={"idea": "一座钟楼每晚倒退一分钟"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        task = generate_chapter_candidate(session, project["chapters"][0]["id"])
    finally:
        update_runtime_model_config(provider="mock", max_tokens=4096, api_key="", routes={"generation": None, "audit": None, "summary": None})
        session_generator.close()

    load_context = next(step for step in task.steps if step.name == "load_context")
    budget = load_context.output_snapshot["context_package"]["context_budget"]

    assert budget["model_max_tokens"] == 2048
    assert budget["reserved_output_tokens"] < 2048
    assert budget["context_budget_tokens"] < 2048
    assert budget["context_budget_tokens"] == budget["total_budget"]
