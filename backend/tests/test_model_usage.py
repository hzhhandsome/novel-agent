from app.models.generation import GenerationRun
from app.services.chapter_service import accept_chapter_candidate, generate_chapter_candidate
from app.services.model_usage import aggregate_model_usage, estimate_model_usage


def test_estimate_model_usage_counts_tokens_duration_and_cost():
    usage = estimate_model_usage(
        node="generate_prose",
        route="generation",
        model_config={"provider": "mock", "model": "mock-writer"},
        input_text="一二三四五六七八",
        output_text="九十",
        duration_ms=25,
        input_cost_per_1k=0.2,
        output_cost_per_1k=0.8,
    )

    assert usage["node"] == "generate_prose"
    assert usage["route"] == "generation"
    assert usage["estimated_input_tokens"] > 0
    assert usage["estimated_output_tokens"] > 0
    assert usage["duration_ms"] == 25
    assert usage["estimated_cost"] > 0
    assert usage["model_config"]["model"] == "mock-writer"


def test_aggregate_model_usage_sums_step_snapshots():
    aggregate = aggregate_model_usage(
        [
            {"generate_prose_model_usage": {"estimated_input_tokens": 10, "estimated_output_tokens": 20, "duration_ms": 5, "estimated_cost": 0.1}},
            {"audit_prose_model_usage": {"estimated_input_tokens": 7, "estimated_output_tokens": 3, "duration_ms": 8, "estimated_cost": 0.2}},
        ]
    )

    assert aggregate["estimated_input_tokens"] == 17
    assert aggregate["estimated_output_tokens"] == 23
    assert aggregate["duration_ms"] == 13
    assert aggregate["estimated_cost"] == 0.3
    assert len(aggregate["calls"]) == 2


def test_generation_records_node_usage_and_run_aggregate(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座桥每晚通向不同年份"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        task = generate_chapter_candidate(session, project["chapters"][0]["id"])
        generate_step = next(step for step in task.steps if step.name == "generate_prose")
        audit_step = next(step for step in task.steps if step.name == "audit_prose")

        assert generate_step.output_snapshot["generate_prose_model_usage"]["estimated_input_tokens"] > 0
        assert audit_step.output_snapshot["audit_prose_model_usage"]["estimated_output_tokens"] > 0

        accept_chapter_candidate(session, project["chapters"][0]["id"])
        run = session.query(GenerationRun).filter(GenerationRun.task_id == task.id).one()
    finally:
        session_generator.close()

    assert run.model_usage_snapshot["estimated_input_tokens"] > 0
    assert run.model_usage_snapshot["estimated_output_tokens"] > 0
    assert len(run.model_usage_snapshot["calls"]) >= 3
