from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.projects import get_project, list_projects
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import create_project_from_idea

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)) -> ProjectRead:
    project = create_project_from_idea(session, payload.idea)
    return ProjectRead.model_validate(project)


@router.get("", response_model=list[ProjectRead])
def read_projects(session: Session = Depends(get_session)) -> list[ProjectRead]:
    return [ProjectRead.model_validate(project) for project in list_projects(session)]


@router.get("/{project_id}", response_model=ProjectRead)
def read_project(project_id: int, session: Session = Depends(get_session)) -> ProjectRead:
    return ProjectRead.model_validate(get_project(session, project_id))
