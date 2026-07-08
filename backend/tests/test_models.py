from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.chapter import Chapter, ChapterStatus
from app.models.project import Project


def test_project_and_chapter_persist_together():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        project = Project(title="临时标题", idea="少年在雨夜捡到一封未来来信")
        session.add(project)
        session.flush()
        chapter = Chapter(project_id=project.id, number=1, title="雨夜来信")
        session.add(chapter)
        session.commit()

        saved = session.get(Chapter, chapter.id)

    assert saved is not None
    assert saved.status == ChapterStatus.not_generated
