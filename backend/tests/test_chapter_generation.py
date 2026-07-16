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
