from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.projects import get_project, list_projects
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.chapter_service import backfill_project_foreshadowing_memory
from app.services.input_review import review_project_idea, review_project_input
from app.services.project_service import create_project_from_idea

router = APIRouter(prefix="/api/projects", tags=["projects"])


class InputReviewRequest(BaseModel):
    input_kind: str
    content: str


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> ProjectRead:
    project = create_project_from_idea(session, payload.idea)
    return ProjectRead.model_validate(project)


@router.post("/input-review")
def review_idea_input(payload: InputReviewRequest) -> dict:
    return review_project_idea(payload.content)


@router.post("/{project_id}/input-review")
def review_existing_project_input(
    project_id: int,
    payload: InputReviewRequest,
    session: Session = Depends(get_session),
) -> dict:
    return review_project_input(session, project_id, payload.input_kind, payload.content)


@router.get("", response_model=list[ProjectRead])
def read_projects(session: Session = Depends(get_session)) -> list[ProjectRead]:
    return [ProjectRead.model_validate(project) for project in list_projects(session)]


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: int, session: Session = Depends(get_session)) -> ProjectRead:
    return ProjectRead.model_validate(get_project(session, project_id))


@router.post("/{project_id}/memory/backfill")
def backfill_project_memory(project_id: int, session: Session = Depends(get_session)) -> dict:
    return backfill_project_foreshadowing_memory(session, project_id)
