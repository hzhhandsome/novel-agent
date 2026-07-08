from typing import TypedDict

from app.services.model_provider import ProjectSetupResult


class ProjectSetupState(TypedDict, total=False):
    idea: str
    setup: ProjectSetupResult | None
    errors: list[str]


class ChapterGenerationState(TypedDict, total=False):
    task_id: int
    project_id: int
    chapter_id: int
    context: str
    chapter_target: str
    prompt_package: str
    generated_content: str
    review_findings: list[dict]
    summary: str
    character_updates: list[str]
    foreshadowing_updates: list[str]
    fail_at: str | None
