from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agent.chapter_graph import build_chapter_generation_graph
from app.models.chapter import Chapter, ChapterStatus
from app.models.generation import GenerationRun, GenerationTask, GenerationTaskStatus, GenerationTaskStep, GenerationTaskStepStatus
from app.models.memory import StoryEvent, WorldRule
from app.services.model_provider import ModelProvider
from app.services.provider_factory import get_model_config_snapshot, get_model_provider_from_snapshot


def generate_chapter_candidate(
    session: Session,
    chapter_id: int,
    fail_at: str | None = None,
    provider: ModelProvider | None = None,
) -> GenerationTask:
    chapter = session.get_one(Chapter, chapter_id)
    chapter.status = ChapterStatus.generating
    task = GenerationTask(
        project_id=chapter.project_id,
        chapter_id=chapter.id,
        kind="chapter_generation",
        model_config_snapshot=get_model_config_snapshot(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return _run_generation_task(session, task.id, fail_at=fail_at, provider=provider)


def stream_chapter_generation_candidate(
    session: Session,
    chapter_id: int,
    provider: ModelProvider | None = None,
    model_config_snapshot: dict | None = None,
) -> Iterator[GenerationTask]:
    chapter = session.get_one(Chapter, chapter_id)
    chapter.status = ChapterStatus.generating
    task = GenerationTask(
        project_id=chapter.project_id,
        chapter_id=chapter.id,
        kind="chapter_generation",
        model_config_snapshot=model_config_snapshot or get_model_config_snapshot(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    yield get_generation_task(session, task.id)

    graph = build_chapter_generation_graph(
        session,
        provider or get_model_provider_from_snapshot(task.model_config_snapshot),
        model_config_snapshot=None if provider else task.model_config_snapshot,
    )
    initial_state = {
        "task_id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "fail_at": None,
    }

    try:
        for _chunk in graph.stream(initial_state):
            yield get_generation_task(session, task.id)
    except Exception:
        session.rollback()
        yield get_generation_task(session, task.id)
        return

    yield get_generation_task(session, task.id)


def stream_auto_generate_chapters(
    session: Session,
    project_id: int,
    chapter_count: int,
    provider: ModelProvider | None = None,
) -> Iterator[dict]:
    if chapter_count < 1:
        raise ValueError("chapter_count must be greater than 0")

    model_config_snapshot = get_model_config_snapshot()
    model_provider = provider or get_model_provider_from_snapshot(model_config_snapshot)
    child_model_config_snapshot = None if provider else model_config_snapshot
    auto_task = GenerationTask(
        project_id=project_id,
        chapter_id=None,
        kind="auto_chapter_generation",
        model_config_snapshot=model_config_snapshot,
    )
    session.add(auto_task)
    session.commit()
    session.refresh(auto_task)

    completed_chapters: list[dict] = []
    current_child_task: GenerationTask | None = None
    yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)

    for index in range(1, chapter_count + 1):
        chapter = _get_or_create_next_chapter(session, project_id)
        step = _get_or_create_step(session, auto_task.id, f"auto_chapter_{index}")
        auto_task.status = GenerationTaskStatus.running
        auto_task.current_step = step.name
        auto_task.chapter_id = chapter.id
        step.status = GenerationTaskStepStatus.running
        step.input_snapshot = {
            "project_id": project_id,
            "chapter_id": chapter.id,
            "chapter_number": chapter.number,
            "index": index,
            "target_count": chapter_count,
        }
        session.commit()
        yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)

        for child_task in stream_chapter_generation_candidate(
            session,
            chapter.id,
            provider=model_provider,
            model_config_snapshot=child_model_config_snapshot,
        ):
            current_child_task = child_task
            yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)

        if current_child_task is None:
            auto_task.status = GenerationTaskStatus.failed
            auto_task.error_type = "MissingChapterTask"
            auto_task.error_message = "chapter generation task was not created"
            step.status = GenerationTaskStepStatus.failed
            step.error_message = auto_task.error_message
            session.commit()
            yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)
            return

        if current_child_task.status == GenerationTaskStatus.failed:
            auto_task.status = GenerationTaskStatus.failed
            auto_task.error_type = current_child_task.error_type or "ChapterGenerationFailed"
            auto_task.error_message = current_child_task.error_message or "chapter generation failed"
            step.status = GenerationTaskStepStatus.failed
            step.error_message = auto_task.error_message
            session.commit()
            yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)
            return

        blocking, blocking_message = _task_has_blocking_audit(current_child_task)
        if blocking:
            auto_task.status = GenerationTaskStatus.paused
            auto_task.error_type = "BlockingAudit"
            auto_task.error_message = blocking_message or "chapter audit blocked automatic acceptance"
            step.status = GenerationTaskStepStatus.failed
            step.error_message = auto_task.error_message
            session.commit()
            yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)
            return

        accepted = accept_chapter_candidate(session, chapter.id)
        completed_chapters.append({"id": accepted.id, "number": accepted.number, "title": accepted.title})
        step.status = GenerationTaskStepStatus.completed
        step.output_snapshot = {
            "chapter_id": accepted.id,
            "chapter_number": accepted.number,
            "chapter_title": accepted.title,
            "generation_task_id": current_child_task.id,
            "accepted": True,
            "completed_count": len(completed_chapters),
            "target_count": chapter_count,
        }
        session.commit()
        yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)

    auto_task.status = GenerationTaskStatus.completed
    auto_task.current_step = f"auto_chapter_{chapter_count}"
    auto_task.error_type = None
    auto_task.error_message = None
    session.commit()
    yield _auto_task_to_dict(session, auto_task, chapter_count, completed_chapters, current_child_task)


def retry_generation_task(
    session: Session,
    task_id: int,
    provider: ModelProvider | None = None,
) -> GenerationTask:
    task = get_generation_task(session, task_id)
    task.status = GenerationTaskStatus.pending
    task.error_type = None
    task.error_message = None
    session.commit()
    return _run_generation_task(
        session,
        task.id,
        fail_at=None,
        provider=provider or get_model_provider_from_snapshot(task.model_config_snapshot),
    )


def get_generation_task(session: Session, task_id: int) -> GenerationTask:
    statement = (
        select(GenerationTask)
        .where(GenerationTask.id == task_id)
        .options(selectinload(GenerationTask.steps), selectinload(GenerationTask.chapter))
    )
    task = session.scalars(statement).one()
    task.steps.sort(key=lambda step: step.id)
    return task


def list_interrupted_tasks(session: Session) -> list[GenerationTask]:
    statement = (
        select(GenerationTask)
        .where(GenerationTask.status.in_([GenerationTaskStatus.failed, GenerationTaskStatus.running]))
        .options(selectinload(GenerationTask.steps), selectinload(GenerationTask.chapter))
        .order_by(GenerationTask.updated_at.desc())
    )
    tasks = list(session.scalars(statement))
    for task in tasks:
        task.steps.sort(key=lambda step: step.id)
    return tasks


def _get_or_create_next_chapter(session: Session, project_id: int) -> Chapter:
    chapters = (
        session.query(Chapter)
        .filter(Chapter.project_id == project_id)
        .order_by(Chapter.number.asc(), Chapter.id.asc())
        .all()
    )
    accepted_numbers = [chapter.number for chapter in chapters if chapter.status == ChapterStatus.accepted]
    next_number = (max(accepted_numbers) if accepted_numbers else 0) + 1
    for chapter in chapters:
        if chapter.number == next_number:
            return chapter

    chapter = Chapter(
        project_id=project_id,
        number=next_number,
        title=f"第 {next_number} 章",
        status=ChapterStatus.not_generated,
    )
    session.add(chapter)
    session.commit()
    session.refresh(chapter)
    return chapter


def _get_or_create_step(session: Session, task_id: int, name: str) -> GenerationTaskStep:
    step = (
        session.query(GenerationTaskStep)
        .filter(GenerationTaskStep.task_id == task_id, GenerationTaskStep.name == name)
        .one_or_none()
    )
    if step is None:
        step = GenerationTaskStep(task_id=task_id, name=name)
        session.add(step)
        session.flush()
    return step


def _task_has_blocking_audit(task: GenerationTask) -> tuple[bool, str | None]:
    for step in task.steps:
        if step.name != "audit_prose" or not step.output_snapshot:
            continue
        audit = step.output_snapshot.get("audit_result") or {}
        findings = audit.get("findings") or []
        for finding in findings:
            if finding.get("blocking"):
                return True, finding.get("message")
    return False, None


def _auto_task_to_dict(
    session: Session,
    auto_task: GenerationTask,
    target_count: int,
    completed_chapters: list[dict],
    current_child_task: GenerationTask | None,
) -> dict:
    task = get_generation_task(session, auto_task.id)
    steps = sorted(task.steps, key=lambda item: item.id)
    return {
        "id": task.id,
        "project_id": task.project_id,
        "kind": task.kind,
        "status": _value(task.status),
        "current_step": task.current_step,
        "error_type": task.error_type,
        "error_message": task.error_message,
        "model_config_snapshot": task.model_config_snapshot,
        "target_count": target_count,
        "completed_count": len(completed_chapters),
        "current_chapter_id": task.chapter_id,
        "current_chapter_task": _generation_task_to_dict(current_child_task) if current_child_task else None,
        "completed_chapters": completed_chapters,
        "steps": [
            {
                "id": step.id,
                "task_id": step.task_id,
                "name": step.name,
                "status": _value(step.status),
                "input_snapshot": step.input_snapshot,
                "output_snapshot": step.output_snapshot,
                "error_message": step.error_message,
            }
            for step in steps
        ],
    }


def accept_chapter_candidate(session: Session, chapter_id: int) -> Chapter:
    chapter = session.get_one(Chapter, chapter_id)
    if not chapter.generated_content:
        raise ValueError("chapter has no generated content to accept")

    chapter.content = chapter.generated_content
    chapter.status = ChapterStatus.accepted
    _record_generation_run(session, chapter_id, accepted=True)
    _commit_structured_memory(session, chapter_id)
    session.commit()
    session.refresh(chapter)
    return chapter


def reject_chapter_candidate(session: Session, chapter_id: int, clear_candidate: bool = False) -> Chapter:
    chapter = session.get_one(Chapter, chapter_id)
    _record_generation_run(session, chapter_id, accepted=False)
    if clear_candidate:
        chapter.generated_content = None
    session.commit()
    session.refresh(chapter)
    return chapter


def _record_generation_run(session: Session, chapter_id: int, accepted: bool) -> None:
    statement = (
        select(GenerationTask)
        .where(GenerationTask.chapter_id == chapter_id, GenerationTask.kind == "chapter_generation")
        .options(selectinload(GenerationTask.steps))
        .order_by(GenerationTask.id.desc())
    )
    task = session.scalars(statement).first()
    if task is None:
        return

    prompt_package = None
    review_result = None
    for step in task.steps:
        if step.name == "build_prompt_package" and step.output_snapshot:
            prompt_package = step.output_snapshot.get("prompt_package")
        if step.name == "audit_prose" and step.output_snapshot:
            review_result = step.output_snapshot.get("audit_result")

    chapter = session.get_one(Chapter, chapter_id)
    session.add(
        GenerationRun(
            task_id=task.id,
            prompt_package=prompt_package,
            output_text=chapter.generated_content,
            review_result=review_result,
            model_config_snapshot=task.model_config_snapshot,
            accepted=accepted,
        )
    )


def _commit_structured_memory(session: Session, chapter_id: int) -> None:
    chapter = session.get_one(Chapter, chapter_id)
    task = _get_latest_chapter_generation_task(session, chapter_id)
    if task is None:
        return

    _commit_story_event(session, chapter)
    _commit_world_rule(session, chapter)
    _commit_character_periods(session, chapter, task)


def _get_latest_chapter_generation_task(session: Session, chapter_id: int) -> GenerationTask | None:
    statement = (
        select(GenerationTask)
        .where(GenerationTask.chapter_id == chapter_id, GenerationTask.kind == "chapter_generation")
        .options(selectinload(GenerationTask.steps), selectinload(GenerationTask.project))
        .order_by(GenerationTask.id.desc())
    )
    return session.scalars(statement).first()


def _commit_story_event(session: Session, chapter: Chapter) -> None:
    existing = (
        session.query(StoryEvent)
        .filter(StoryEvent.project_id == chapter.project_id, StoryEvent.source_chapter_id == chapter.id)
        .one_or_none()
    )
    summary = chapter.summary or chapter.generated_content or chapter.content or ""
    if existing or not summary:
        return

    character_names = "、".join(character.name for character in chapter.project.characters)
    session.add(
        StoryEvent(
            project_id=chapter.project_id,
            source_chapter_id=chapter.id,
            title=f"第 {chapter.number} 章：{chapter.title}",
            summary=summary,
            characters=character_names or None,
            location=None,
            consequence="已采纳章节形成的正式剧情事实。",
        )
    )


def _commit_world_rule(session: Session, chapter: Chapter) -> None:
    existing = (
        session.query(WorldRule)
        .filter(WorldRule.project_id == chapter.project_id, WorldRule.source_chapter_id == chapter.id)
        .one_or_none()
    )
    summary = chapter.summary or ""
    if existing or not summary:
        return

    session.add(
        WorldRule(
            project_id=chapter.project_id,
            source_chapter_id=chapter.id,
            rule=summary,
            limitation="采纳章节提取的正式世界观或剧情约束，后续生成需要保持一致。",
            exception=None,
            status="active",
        )
    )


def _commit_character_periods(session: Session, chapter: Chapter, task: GenerationTask) -> None:
    decisions = _step_output(task, "judge_character_period").get("character_period_decisions", {})
    if not decisions:
        return

    period_cards = decisions.get("new_period_cards") or []
    if isinstance(period_cards, list):
        for card in period_cards:
            if isinstance(card, dict):
                _apply_character_period_card(chapter, card)

    text_updates = _string_items(decisions.get("updates"))
    text_updates.extend(_string_items(decisions.get("memory_changes")))
    text_updates.extend(_string_items(decisions.get("relationship_changes")))
    if not text_updates and not decisions.get("stage_changed"):
        return

    target = chapter.project.characters[0] if chapter.project.characters else None
    if target is None:
        return

    target.period_summary = "；".join(text_updates) if text_updates else target.period_summary
    target.period_source_chapter_id = chapter.id
    if decisions.get("stage_changed") and not target.period_stage:
        target.period_stage = "新阶段"


def _apply_character_period_card(chapter: Chapter, card: dict) -> None:
    name = str(card.get("character") or card.get("name") or "")
    target = next((character for character in chapter.project.characters if character.name == name), None)
    if target is None:
        return

    stage = card.get("stage") or card.get("period_stage") or card.get("stage_name")
    summary = card.get("summary") or card.get("period_summary")
    current_goal = card.get("current_goal")
    key_memories = card.get("key_memories") or card.get("memory")
    relationships = card.get("relationships") or card.get("relationship_changes")

    if stage:
        target.period_stage = str(stage)
    if summary:
        target.period_summary = str(summary)
    if current_goal:
        target.current_goal = str(current_goal)
    if key_memories:
        target.key_memories = str(key_memories)
    if relationships:
        target.relationships = str(relationships)
    target.period_source_chapter_id = chapter.id


def _step_output(task: GenerationTask, name: str) -> dict:
    for step in task.steps:
        if step.name == name and step.output_snapshot:
            return step.output_snapshot
    return {}


def _string_items(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _run_generation_task(
    session: Session,
    task_id: int,
    fail_at: str | None,
    provider: ModelProvider | None,
) -> GenerationTask:
    task = get_generation_task(session, task_id)
    graph = build_chapter_generation_graph(
        session,
        provider or get_model_provider_from_snapshot(task.model_config_snapshot),
        model_config_snapshot=None if provider else task.model_config_snapshot,
    )
    initial_state = {
        "task_id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "fail_at": fail_at,
    }

    try:
        graph.invoke(initial_state)
    except Exception:
        session.rollback()
        return get_generation_task(session, task.id)

    return get_generation_task(session, task.id)


def _generation_task_to_dict(task: GenerationTask) -> dict:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "kind": task.kind,
        "status": _value(task.status),
        "current_step": task.current_step,
        "error_type": task.error_type,
        "error_message": task.error_message,
        "model_config_snapshot": task.model_config_snapshot,
        "chapter": _chapter_to_dict(task.chapter) if task.chapter else None,
        "steps": [
            {
                "id": step.id,
                "task_id": step.task_id,
                "name": step.name,
                "status": _value(step.status),
                "input_snapshot": step.input_snapshot,
                "output_snapshot": step.output_snapshot,
                "error_message": step.error_message,
            }
            for step in task.steps
        ],
    }


def _chapter_to_dict(chapter: Chapter) -> dict:
    return {
        "id": chapter.id,
        "project_id": chapter.project_id,
        "number": chapter.number,
        "title": chapter.title,
        "status": _value(chapter.status),
        "content": chapter.content,
        "generated_content": chapter.generated_content,
        "summary": chapter.summary,
    }


def _value(value):
    return value.value if hasattr(value, "value") else value
