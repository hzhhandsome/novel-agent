from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.chapters import update_chapter_content
from app.schemas.chapter import ChapterRead, ChapterUpdate
from app.services.chapter_service import accept_chapter_candidate, reject_chapter_candidate

router = APIRouter(prefix="/api/chapters", tags=["chapters"])


@router.patch("/{chapter_id}", response_model=ChapterRead)
def update_chapter(
    chapter_id: int,
    payload: ChapterUpdate,
    session: Session = Depends(get_session),
) -> ChapterRead:
    chapter = update_chapter_content(session, chapter_id, payload.title, payload.content)
    return ChapterRead.model_validate(chapter)


@router.post("/{chapter_id}/accept", response_model=ChapterRead)
def accept_chapter(chapter_id: int, session: Session = Depends(get_session)) -> ChapterRead:
    chapter = accept_chapter_candidate(session, chapter_id)
    return ChapterRead.model_validate(chapter)


@router.post("/{chapter_id}/reject", response_model=ChapterRead)
def reject_chapter(chapter_id: int, session: Session = Depends(get_session)) -> ChapterRead:
    chapter = reject_chapter_candidate(session, chapter_id)
    return ChapterRead.model_validate(chapter)
