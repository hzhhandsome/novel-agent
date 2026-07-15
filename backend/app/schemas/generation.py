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
    steps: list[TaskStepRead] = []

    model_config = ConfigDict(from_attributes=True)
