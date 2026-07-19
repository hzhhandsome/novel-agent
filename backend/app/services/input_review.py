from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.provider_factory import get_model_config_snapshot, get_model_provider_from_snapshot


def review_project_idea(content: str) -> dict:
    provider = get_model_provider_from_snapshot(get_model_config_snapshot(), route="audit")
    result = provider.review_user_input("project_idea", content, "")
    return _review_to_dict(result, project_id=None, input_kind="project_idea")


def review_project_input(session: Session, project_id: int, input_kind: str, content: str) -> dict:
    project = session.get_one(Project, project_id)
    provider = get_model_provider_from_snapshot(get_model_config_snapshot(), route="audit")
    result = provider.review_user_input(input_kind, content, _project_context(project))
    return _review_to_dict(result, project_id=project_id, input_kind=input_kind)


def _project_context(project: Project) -> str:
    summaries = "；".join(
        f"第 {chapter.number} 章：{chapter.summary}"
        for chapter in sorted(project.chapters, key=lambda item: item.number)
        if chapter.summary
    )
    foreshadowing = "；".join(item.content for item in project.foreshadowing_items)
    characters = "；".join(f"{item.name}：{item.current_goal}" for item in project.characters)
    return "\n".join(
        [
            f"小说定位：{project.positioning or ''}",
            f"世界观：{project.worldview or ''}",
            f"主线：{project.main_plot or ''}",
            f"角色：{characters}",
            f"已采纳摘要：{summaries}",
            f"伏笔：{foreshadowing}",
        ]
    )


def _review_to_dict(result, project_id: int | None, input_kind: str) -> dict:
    return {
        "project_id": project_id,
        "input_kind": input_kind,
        "decision": result.decision,
        "reason": result.reason,
        "suggestions": result.suggestions,
    }
