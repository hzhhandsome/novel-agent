from app.models.generation import GenerationTaskStatus
from app.services.chapter_service import generate_chapter_candidate, retry_generation_task
from app.services.provider_factory import get_current_model_config, update_runtime_model_config


def test_model_config_api_updates_runtime_config_without_returning_secret(client_with_db):
    try:
        response = client_with_db.put(
            "/api/model-config",
            json={
                "provider": "deepseek",
                "base_url": "https://api.deepseek.com/anthropic",
                "model": "deepseek-v4-flash",
                "max_tokens": 2048,
                "api_key": "secret-key",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["provider"] == "deepseek"
        assert payload["base_url"] == "https://api.deepseek.com/anthropic"
        assert payload["model"] == "deepseek-v4-flash"
        assert payload["max_tokens"] == 2048
        assert payload["api_key_set"] is True
        assert "secret-key" not in response.text

        current = client_with_db.get("/api/model-config").json()
        assert current["provider"] == "deepseek"
        assert current["api_key_set"] is True
    finally:
        update_runtime_model_config(provider="mock", api_key="")


def test_model_config_api_updates_route_overrides_without_returning_secret(client_with_db):
    try:
        response = client_with_db.put(
            "/api/model-config",
            json={
                "provider": "mock",
                "model": "default-model",
                "max_tokens": 4096,
                "routes": {
                    "generation": {"model": "writer-model", "max_tokens": 8192},
                    "audit": {"model": "audit-model", "api_key": "route-secret"},
                    "summary": {"model": "summary-model"},
                },
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["model"] == "default-model"
        assert payload["routes"]["generation"]["model"] == "writer-model"
        assert payload["routes"]["generation"]["max_tokens"] == 8192
        assert payload["routes"]["audit"]["model"] == "audit-model"
        assert payload["routes"]["summary"]["model"] == "summary-model"
        assert "route-secret" not in response.text

        current = client_with_db.get("/api/model-config").json()
        assert current["routes"]["generation"]["model"] == "writer-model"
    finally:
        update_runtime_model_config(provider="mock", api_key="", routes={"generation": None, "audit": None, "summary": None})


def test_new_generation_task_records_current_model_snapshot(client_with_db):
    update_runtime_model_config(provider="mock", api_key="")
    project = client_with_db.post("/api/projects", json={"idea": "一盏路灯开始记忆路过的人"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        task = generate_chapter_candidate(session, project["chapters"][0]["id"])
    finally:
        session_generator.close()

    assert task.model_config_snapshot["provider"] == "mock"
    assert task.model_config_snapshot["model"]
    assert "api_key" not in task.model_config_snapshot


def test_new_generation_task_records_model_route_snapshot(client_with_db):
    update_runtime_model_config(
        provider="mock",
        model="default-model",
        api_key="",
        routes={"generation": {"model": "writer-model"}, "audit": {"model": "audit-model"}},
    )
    project = client_with_db.post("/api/projects", json={"idea": "一盏路灯开始记忆路过的人"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        task = generate_chapter_candidate(session, project["chapters"][0]["id"], fail_at="load_context")
    finally:
        update_runtime_model_config(provider="mock", api_key="", routes={"generation": None, "audit": None, "summary": None})
        session_generator.close()

    assert task.model_config_snapshot["model"] == "default-model"
    assert task.model_config_snapshot["routes"]["generation"]["model"] == "writer-model"
    assert task.model_config_snapshot["routes"]["audit"]["model"] == "audit-model"
    assert "api_key" not in task.model_config_snapshot["routes"]["generation"]


def test_retry_uses_task_snapshot_after_runtime_model_switch(client_with_db):
    update_runtime_model_config(provider="mock", api_key="")
    project = client_with_db.post("/api/projects", json={"idea": "一盏路灯开始记忆路过的人"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        failed_task = generate_chapter_candidate(session, project["chapters"][0]["id"], fail_at="generate_prose")
        assert failed_task.status == GenerationTaskStatus.failed
        assert failed_task.model_config_snapshot["provider"] == "mock"

        update_runtime_model_config(provider="deepseek", api_key="")
        retried = retry_generation_task(session, failed_task.id)
    finally:
        update_runtime_model_config(provider="mock", api_key="")
        session_generator.close()

    assert retried.status == GenerationTaskStatus.completed
    assert retried.model_config_snapshot["provider"] == "mock"
    assert get_current_model_config()["provider"] == "mock"
