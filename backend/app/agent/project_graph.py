from langgraph.graph import END, StateGraph

from app.agent.state import ProjectSetupState
from app.services.model_provider import ModelProvider


def build_project_setup_graph(provider: ModelProvider):
    workflow = StateGraph(ProjectSetupState)

    def generate_setup(state: ProjectSetupState) -> ProjectSetupState:
        setup = provider.generate_project_setup(state["idea"])
        return {"setup": setup, "errors": []}

    workflow.add_node("generate_setup", generate_setup)
    workflow.set_entry_point("generate_setup")
    workflow.add_edge("generate_setup", END)
    return workflow.compile()
