from app.models.foreshadowing import ForeshadowingItem, ForeshadowingStatus
from app.services.tool_registry import get_internal_tool_registry


def test_tool_registry_rejects_missing_required_argument(client_with_db):
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)
    try:
        registry = get_internal_tool_registry(session)
        record = registry.call("list_open_foreshadowing", {"project_id": None}, task_id=1, step_name="load_context")
    finally:
        session_generator.close()

    assert record["status"] == "failed"
    assert record["tool_name"] == "list_open_foreshadowing"
    assert record["error_type"] == "ToolCallValidationError"
    assert "project_id" in record["error"]
    assert record["duration_ms"] >= 0


def test_list_open_foreshadowing_returns_read_only_summary(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个失忆修书人修补会改变现实的书"},
    ).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)
    try:
        session.add(
            ForeshadowingItem(
                project_id=project["id"],
                content="红封书页上的未知批注",
                status=ForeshadowingStatus.planted,
                notes="等待后续推进",
            )
        )
        session.add(
            ForeshadowingItem(
                project_id=project["id"],
                content="已经回收的旧伏笔",
                status=ForeshadowingStatus.recovered,
            )
        )
        session.commit()

        registry = get_internal_tool_registry(session)
        record = registry.call(
            "list_open_foreshadowing",
            {"project_id": project["id"]},
            task_id=1,
            step_name="judge_foreshadowing",
        )
    finally:
        session_generator.close()

    assert record["status"] == "completed"
    assert record["tool_name"] == "list_open_foreshadowing"
    assert record["result_summary"] == "items=1"
    assert record["result"]["items"][0]["content"] == "红封书页上的未知批注"
    assert "已经回收的旧伏笔" not in str(record["result"])
    assert record["duration_ms"] >= 0
