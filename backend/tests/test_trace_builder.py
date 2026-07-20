from app.models.generation import GenerationTask
from app.services.chapter_service import generate_chapter_candidate
from app.services.trace_builder import build_task_trace


def test_build_task_trace_includes_steps_model_retrieval_tool_and_persistence(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"},
    ).json()
    chapter_id = project["chapters"][0]["id"]
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        task = generate_chapter_candidate(session, chapter_id)
        trace = build_task_trace(task)
    finally:
        session_generator.close()

    assert trace["trace_id"] == f"generation-task-{task.id}"
    assert trace["root_span_id"] == f"task-{task.id}"
    assert any(event["event_type"] == "task" for event in trace["events"])
    assert any(event["event_type"] == "step" and event["name"] == "load_context" for event in trace["events"])
    assert any(event["event_type"] == "llm_call" and event["name"] == "generate_prose" for event in trace["events"])
    assert any(event["event_type"] == "retrieval" for event in trace["events"])
    assert any(event["event_type"] == "tool_call" for event in trace["events"])
    assert any(event["event_type"] == "persistence" for event in trace["events"])

    llm_event = next(event for event in trace["events"] if event["event_type"] == "llm_call" and event["name"] == "generate_prose")
    assert llm_event["parent_span_id"].startswith("step-")
    assert llm_event["metadata"]["estimated_input_tokens"] > 0
    assert llm_event["duration_ms"] >= 0


def test_build_task_trace_includes_failed_step_error(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个邮差给梦境投递真实信件"},
    ).json()
    chapter_id = project["chapters"][0]["id"]
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)
    try:
        task = generate_chapter_candidate(session, chapter_id, fail_at="audit_prose")
        assert str(task.status.value if hasattr(task.status, "value") else task.status) == "failed"
        task = session.query(GenerationTask).one()
        trace = build_task_trace(task)
    finally:
        session_generator.close()

    failed_step = next(event for event in trace["events"] if event["event_type"] == "step" and event["name"] == "audit_prose")
    assert failed_step["status"] == "failed"
    assert failed_step["metadata"]["error_message"]
