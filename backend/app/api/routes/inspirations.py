from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models.inspiration import Inspiration
from app.schemas.project import InspirationCreate, InspirationRead

router = APIRouter(prefix="/api/projects", tags=["inspirations"])


@router.post("/{project_id}/inspirations", response_model=InspirationRead, status_code=status.HTTP_201_CREATED)
def create_inspiration(
    project_id: int,
    payload: InspirationCreate,
    session: Session = Depends(get_session),
) -> InspirationRead:
    inspiration = Inspiration(project_id=project_id, content=payload.content, applied=False)
    session.add(inspiration)
    session.commit()
    session.refresh(inspiration)
    return InspirationRead.model_validate(inspiration)
