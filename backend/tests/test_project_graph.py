from app.agent.project_graph import build_project_setup_graph
from app.services.model_provider import MockModelProvider


def test_project_graph_generates_setup_artifacts():
    graph = build_project_setup_graph(MockModelProvider())

    result = graph.invoke({"idea": "一个海边小镇每天凌晨都会收到未来新闻"})

    assert result["setup"].positioning
    assert result["setup"].worldview
    assert len(result["setup"].chapters) >= 3
