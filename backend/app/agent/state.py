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
    context_package: dict
    tool_calls: list[dict]
    chapter_target: str
    prompt_package: str
    prompt_metadata: dict
    generated_content: str
    draft_summary: str
    review_findings: list[dict]
    audit_result: dict
    summary: str
    summary_result: dict
    generation_model_config: dict
    audit_model_config: dict
    summary_model_config: dict
    generate_prose_prompt_metadata: dict
    audit_prose_prompt_metadata: dict
    summarize_chapter_prompt_metadata: dict
    judge_foreshadowing_prompt_metadata: dict
    judge_character_period_prompt_metadata: dict
    propose_future_plan_updates_prompt_metadata: dict
    generate_prose_model_usage: dict
    audit_prose_model_usage: dict
    summarize_chapter_model_usage: dict
    judge_foreshadowing_model_usage: dict
    judge_character_period_model_usage: dict
    propose_future_plan_updates_model_usage: dict
    character_updates: list[str]
    foreshadowing_updates: list[str]
    foreshadowing_decisions: dict
    character_period_decisions: dict
    future_plan_updates: dict
    candidate_result: dict
    persistence_result: dict
    fail_at: str | None
