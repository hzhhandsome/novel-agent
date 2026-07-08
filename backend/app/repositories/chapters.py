from sqlalchemy.orm import Session

from app.models.chapter import Chapter


def get_chapter(session: Session, chapter_id: int) -> Chapter:
    return session.get_one(Chapter, chapter_id)


def update_chapter_content(
    session: Session,
    chapter_id: int,
    title: str | None,
    content: str | None,
) -> Chapter:
    chapter = get_chapter(session, chapter_id)
    if title is not None:
        chapter.title = title
    if content is not None:
        chapter.content = content
    session.commit()
    session.refresh(chapter)
    return chapter
