from app.services.provider_factory import (
    get_model_config_snapshot,
    get_model_provider_from_snapshot,
    update_runtime_model_config,
)


def test_provider_factory_selects_route_specific_snapshot_provider():
    update_runtime_model_config(
        provider="deepseek",
        base_url="https://api.deepseek.com/anthropic",
        model="default-model",
        max_tokens=4096,
        api_key="secret-key",
        routes={"generation": {"model": "writer-model", "max_tokens": 8192}},
    )

    try:
        snapshot = get_model_config_snapshot()
        provider = get_model_provider_from_snapshot(snapshot, route="generation")
    finally:
        update_runtime_model_config(provider="mock", api_key="", routes={"generation": None, "audit": None, "summary": None})

    assert provider.model == "writer-model"
    assert provider.max_tokens == 8192


def test_routed_nodes_record_model_route_snapshots(client_with_db):
    update_runtime_model_config(
        provider="mock",
        model="default-model",
        api_key="",
        routes={
            "generation": {"model": "writer-model"},
            "audit": {"model": "audit-model"},
            "summary": {"model": "summary-model"},
        },
    )
    project = client_with_db.post("/api/projects", json={"idea": "一座钟楼会倒流人的承诺"}).json()

    try:
        response = client_with_db.post(f"/api/chapters/{project['chapters'][0]['id']}/generate")
    finally:
        update_runtime_model_config(provider="mock", api_key="", routes={"generation": None, "audit": None, "summary": None})

    assert response.status_code == 200
    task = response.json()
    steps = {step["name"]: step["output_snapshot"] for step in task["steps"]}
    assert steps["generate_prose"]["generation_model_config"]["model"] == "writer-model"
    assert steps["audit_prose"]["audit_model_config"]["model"] == "audit-model"
    assert steps["summarize_chapter"]["summary_model_config"]["model"] == "summary-model"
