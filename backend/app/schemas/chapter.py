from pydantic import BaseModel, ConfigDict

from app.models.chapter import ChapterStatus


class ChapterRead(BaseModel):
    id: int
    project_id: int
    number: int
    title: str
    status: ChapterStatus
    content: str | None = None
    generated_content: str | None = None
    summary: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ChapterUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
