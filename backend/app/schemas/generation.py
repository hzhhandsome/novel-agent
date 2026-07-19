from pydantic import BaseModel, ConfigDict


class TaskStepRead(BaseModel):
    id: int
    task_id: int
    name: str
    status: str
    input_snapshot: dict | None = None
    output_snapshot: dict | None = None
    error_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskRead(BaseModel):
    id: int
    project_id: int
    chapter_id: int | None = None
    kind: str
    status: str
    current_step: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    model_config_snapshot: dict | None = None
    steps: list[TaskStepRead] = []

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelConfigRead(BaseModel):
    provider: str
    base_url: str
    model: str
    max_tokens: int
    api_key_set: bool


class ModelConfigUpdate(BaseModel):
    provider: str | None = None
    base_url: str | None = None
    model: str | None = None
    max_tokens: int | None = None
    api_key: str | None = None
