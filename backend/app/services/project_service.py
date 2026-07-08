from sqlalchemy.orm import Session

from app.models.project import Project
from app.agent.project_graph import build_project_setup_graph
from app.repositories.projects import (
    create_project_with_seed,
)
from app.services.model_provider import ModelProvider
from app.services.provider_factory import get_model_provider


def create_project_from_idea(
    session: Session,
    idea: str,
    provider: ModelProvider | None = None,
) -> Project:
    graph = build_project_setup_graph(provider or get_model_provider())
    state = graph.invoke({"idea": idea, "errors": []})
    setup = state["setup"]
    return create_project_with_seed(session, idea, setup)
