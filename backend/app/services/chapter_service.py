from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agent.chapter_graph import build_chapter_generation_graph, persist_generation_result
from app.models.chapter import Chapter, ChapterStatus
from app.models.generation import GenerationRun, GenerationTask, GenerationTaskStatus
from app.services.model_provider import MockModelProvider, ModelProvider


def generate_chapter_candidate(
    session: Session,
    chapter_id: int,
    fail_at: str | None = None,
    provider: ModelProvider | None = None,
) -> GenerationTask:
    chapter = session.get_one(Chapter, chapter_id)
    chapter.status = ChapterStatus.generating
    task = GenerationTask(project_id=chapter.project_id, chapter_id=chapter.id, kind="chapter_generation")
    session.add(task)
    session.commit()
    session.refresh(task)
    return _run_generation_task(session, task.id, fail_at=fail_at, provider=provider)


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
    return _run_generation_task(session, task.id, fail_at=None, provider=provider)


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


def accept_chapter_candidate(session: Session, chapter_id: int) -> Chapter:
    chapter = session.get_one(Chapter, chapter_id)
    if not chapter.generated_content:
        raise ValueError("chapter has no generated content to accept")

    chapter.content = chapter.generated_content
    chapter.status = ChapterStatus.accepted
    _record_generation_run(session, chapter_id, accepted=True)
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
        if step.name == "review_prose" and step.output_snapshot:
            review_result = {"findings": step.output_snapshot.get("review_findings", [])}

    chapter = session.get_one(Chapter, chapter_id)
    session.add(
        GenerationRun(
            task_id=task.id,
            prompt_package=prompt_package,
            output_text=chapter.generated_content,
            review_result=review_result,
            accepted=accepted,
        )
    )


def _run_generation_task(
    session: Session,
    task_id: int,
    fail_at: str | None,
    provider: ModelProvider | None,
) -> GenerationTask:
    task = get_generation_task(session, task_id)
    graph = build_chapter_generation_graph(session, provider or MockModelProvider())
    initial_state = {
        "task_id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "fail_at": fail_at,
    }

    try:
        final_state = graph.invoke(initial_state)
    except Exception:
        session.rollback()
        return get_generation_task(session, task.id)

    persist_generation_result(session, final_state)
    return get_generation_task(session, task.id)
