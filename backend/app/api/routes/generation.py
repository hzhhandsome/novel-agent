import json

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.chapter import Chapter
from app.models.generation import GenerationTask
from app.services.chapter_service import (
    generate_chapter_candidate,
    get_generation_task,
    list_interrupted_tasks,
    retry_generation_task,
    stream_chapter_generation_candidate,
)

router = APIRouter(tags=["generation"])


class GenerateChapterRequest(BaseModel):
    fail_at: str | None = None


@router.post("/api/chapters/{chapter_id}/generate")
def generate_chapter(
    chapter_id: int,
    payload: GenerateChapterRequest | None = None,
    session: Session = Depends(get_session),
) -> dict:
    task = generate_chapter_candidate(session, chapter_id, fail_at=payload.fail_at if payload else None)
    return _task_to_dict(task)


@router.post("/api/chapters/{chapter_id}/generate/stream")
def generate_chapter_stream(
    chapter_id: int,
    session: Session = Depends(get_session),
) -> StreamingResponse:
    def events():
        for task in stream_chapter_generation_candidate(session, chapter_id):
            yield "event: task\n"
            yield f"data: {json.dumps(_task_to_dict(task), ensure_ascii=False)}\n\n"
        yield "event: done\n"
        yield "data: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


@router.get("/api/generation-tasks/interrupted")
def read_interrupted_tasks(session: Session = Depends(get_session)) -> list[dict]:
    return [_task_to_dict(task) for task in list_interrupted_tasks(session)]


@router.get("/api/generation-tasks/{task_id}")
def read_generation_task(task_id: int, session: Session = Depends(get_session)) -> dict:
    return _task_to_dict(get_generation_task(session, task_id))


@router.post("/api/generation-tasks/{task_id}/retry")
def retry_task(task_id: int, session: Session = Depends(get_session)) -> dict:
    task = retry_generation_task(session, task_id)
    return _task_to_dict(task)


def _task_to_dict(task: GenerationTask) -> dict:
    return {
        "id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "kind": task.kind,
        "status": _value(task.status),
        "current_step": task.current_step,
        "error_type": task.error_type,
        "error_message": task.error_message,
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
