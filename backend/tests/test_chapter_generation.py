from app.models.foreshadowing import ForeshadowingItem, ForeshadowingStatus
from app.services.chapter_service import generate_chapter_candidate
from app.services.model_provider import MockModelProvider


class BrokenCharacterPeriodProvider(MockModelProvider):
    def judge_character_period(self, content: str, context: str, characters: list[str]) -> dict:
        raise ValueError("Expecting ',' delimiter: line 8 column 23 (char 207)")


def test_generate_chapter_records_steps_and_generated_content(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"}).json()
    chapter_id = project["chapters"][0]["id"]

    response = client_with_db.post(f"/api/chapters/{chapter_id}/generate")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["chapter"]["generated_content"]
    trace = body["trace"]
    assert trace["trace_id"] == f"generation-task-{body['id']}"
    assert any(event["event_type"] == "llm_call" for event in trace["events"])
    assert any(event["event_type"] == "tool_call" for event in trace["events"])
    step_names = [step["name"] for step in body["steps"]]
    assert step_names == [
        "load_context",
        "build_chapter_target",
        "build_prompt_package",
        "generate_prose",
        "audit_prose",
        "summarize_chapter",
        "judge_foreshadowing",
        "judge_character_period",
        "propose_future_plan_updates",
        "build_candidate_result",
        "persist_candidate_result",
    ]
    assert step_names.index("audit_prose") < step_names.index("summarize_chapter")
    assert all(step["output_snapshot"] for step in body["steps"])
    load_context = next(step for step in body["steps"] if step["name"] == "load_context")
    prompt_step = next(step for step in body["steps"] if step["name"] == "build_prompt_package")
    generate_step = next(step for step in body["steps"] if step["name"] == "generate_prose")
    audit_step = next(step for step in body["steps"] if step["name"] == "audit_prose")
    foreshadowing_step = next(step for step in body["steps"] if step["name"] == "judge_foreshadowing")

    load_context_calls = load_context["output_snapshot"]["tool_calls"]
    assert any(call["tool_name"] == "list_open_foreshadowing" for call in load_context_calls)
    assert all(call["status"] == "completed" for call in load_context_calls)
    foreshadowing_calls = foreshadowing_step["output_snapshot"]["tool_calls"]
    assert any(call["tool_name"] == "list_open_foreshadowing" for call in foreshadowing_calls)

    assert prompt_step["output_snapshot"]["prompt_metadata"]["prompt_version"].startswith("build_prompt_package@")
    assert generate_step["output_snapshot"]["generate_prose_prompt_metadata"]["prompt_version"].startswith("generate_prose@")
    assert audit_step["output_snapshot"]["audit_prose_prompt_metadata"]["prompt_version"].startswith("audit_prose@")
    assert len(generate_step["output_snapshot"]["generate_prose_prompt_metadata"]["prompt_hash"]) == 64

    candidate_step = next(step for step in body["steps"] if step["name"] == "build_candidate_result")
    candidate = candidate_step["output_snapshot"]["candidate_result"]
    assert candidate["summary"]
    assert candidate["audit"]["findings"]
    assert candidate["foreshadowing"]["advanced"]
    assert candidate["character_period"]["updates"]
    assert candidate["future_plan"]["suggestions"]


def test_character_period_json_failure_does_not_abort_generation(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一个邮差给梦境投递真实信件"}).json()
    chapter_id = project["chapters"][0]["id"]
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        task = generate_chapter_candidate(
            session,
            chapter_id,
            provider=BrokenCharacterPeriodProvider(),
        )
    finally:
        session_generator.close()

    assert task.status == "completed"
    character_step = next(step for step in task.steps if step.name == "judge_character_period")
    decisions = character_step.output_snapshot["character_period_decisions"]
    assert decisions["skipped"] is True
    assert "Expecting ',' delimiter" in decisions["error"]


def test_tool_call_empty_foreshadowing_result_does_not_restore_recovered_items(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一个邮差给梦境投递真实信件"}).json()
    chapter_id = project["chapters"][0]["id"]
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        session.add(
            ForeshadowingItem(
                project_id=project["id"],
                content="已经回收的梦境邮戳",
                status=ForeshadowingStatus.recovered,
            )
        )
        session.commit()
        task = generate_chapter_candidate(session, chapter_id)
    finally:
        session_generator.close()

    load_context = next(step for step in task.steps if step.name == "load_context")
    assert load_context.output_snapshot["context_package"]["foreshadowing_items"] == []
    judge_step = next(step for step in task.steps if step.name == "judge_foreshadowing")
    assert "已经回收的梦境邮戳" not in str(judge_step.output_snapshot)


def test_generate_chapter_stream_emits_node_progress(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"}).json()
    chapter_id = project["chapters"][0]["id"]

    response = client_with_db.post(f"/api/chapters/{chapter_id}/generate/stream")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    text = response.text
    assert "event: task" in text
    assert "event: done" in text
    assert '"name": "load_context"' in text
    assert '"name": "persist_candidate_result"' in text
    assert '"status": "completed"' in text

    expected_order = [
        "load_context",
        "build_chapter_target",
        "build_prompt_package",
        "generate_prose",
        "audit_prose",
        "summarize_chapter",
        "judge_foreshadowing",
        "judge_character_period",
        "propose_future_plan_updates",
        "build_candidate_result",
        "persist_candidate_result",
    ]
    last_index = -1
    for name in expected_order:
        index = text.find(f'"name": "{name}"')
        assert index > last_index
        last_index = index
