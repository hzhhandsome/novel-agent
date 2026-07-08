from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chapter import ChapterRead


class ProjectCreate(BaseModel):
    idea: str = Field(min_length=1)
    genre: str | None = None
    style: str | None = None


class CharacterRead(BaseModel):
    id: int
    project_id: int
    name: str
    role: str | None = None
    personality: str | None = None
    current_goal: str | None = None
    key_memories: str | None = None
    relationships: str | None = None
    writing_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ForeshadowingRead(BaseModel):
    id: int
    project_id: int
    source_chapter_id: int | None = None
    content: str
    status: str
    notes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InspirationRead(BaseModel):
    id: int
    project_id: int
    content: str
    applied: bool

    model_config = ConfigDict(from_attributes=True)


class InspirationCreate(BaseModel):
    content: str = Field(min_length=1)


class ProjectRead(BaseModel):
    id: int
    title: str
    idea: str
    positioning: str | None = None
    worldview: str | None = None
    main_plot: str | None = None
    chapters: list[ChapterRead] = []
    characters: list[CharacterRead] = []
    foreshadowing_items: list[ForeshadowingRead] = []
    inspirations: list[InspirationRead] = []

    model_config = ConfigDict(from_attributes=True)
