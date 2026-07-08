from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chapter import Chapter
from app.models.character import Character
from app.models.project import Project


@dataclass(frozen=True)
class ChapterSeed:
    number: int
    title: str


@dataclass(frozen=True)
class CharacterSeed:
    name: str
    role: str
    personality: str
    current_goal: str
    key_memories: str
    relationships: str
    writing_notes: str


@dataclass(frozen=True)
class ProjectSeed:
    title: str
    positioning: str
    worldview: str
    main_plot: str
    chapters: list[ChapterSeed]
    characters: list[CharacterSeed]


def create_project_with_seed(session: Session, idea: str, setup_result: ProjectSeed) -> Project:
    project = Project(
        title=setup_result.title,
        idea=idea,
        positioning=setup_result.positioning,
        worldview=setup_result.worldview,
        main_plot=setup_result.main_plot,
    )
    session.add(project)
    session.flush()

    for chapter_seed in setup_result.chapters:
        session.add(
            Chapter(
                project_id=project.id,
                number=chapter_seed.number,
                title=chapter_seed.title,
            )
        )

    for character_seed in setup_result.characters:
        session.add(
            Character(
                project_id=project.id,
                name=character_seed.name,
                role=character_seed.role,
                personality=character_seed.personality,
                current_goal=character_seed.current_goal,
                key_memories=character_seed.key_memories,
                relationships=character_seed.relationships,
                writing_notes=character_seed.writing_notes,
            )
        )

    session.commit()
    return get_project(session, project.id)


def get_project(session: Session, project_id: int) -> Project:
    statement = (
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.chapters),
            selectinload(Project.characters),
            selectinload(Project.foreshadowing_items),
            selectinload(Project.inspirations),
        )
    )
    project = session.scalars(statement).one()
    project.chapters.sort(key=lambda chapter: chapter.number)
    return project


def list_projects(session: Session) -> list[Project]:
    statement = select(Project).order_by(Project.id.desc())
    return list(session.scalars(statement))
