import json

from app.services.chapter_service import accept_chapter_candidate, generate_chapter_candidate
from app.services.training_data import export_training_examples, write_training_jsonl
from app.training_data.export import export_training_data


def test_export_training_examples_from_accepted_generation_runs(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座灯塔会记录每个失踪者的影子"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        generate_chapter_candidate(session, project["chapters"][0]["id"])
        accept_chapter_candidate(session, project["chapters"][0]["id"])

        examples = export_training_examples(session)
    finally:
        session_generator.close()

    task_types = {example["task_type"] for example in examples}
    assert {"context_to_chapter", "chapter_to_summary", "chapter_to_audit"}.issubset(task_types)
    assert all(example["metadata"]["accepted"] is True for example in examples)
    assert "api_key" not in json.dumps(examples, ensure_ascii=False)


def test_write_training_jsonl_writes_one_json_object_per_line(tmp_path):
    output_path = tmp_path / "training.jsonl"
    count = write_training_jsonl(
        [
            {"task_type": "context_to_chapter", "input": {"prompt": "a"}, "output": {"content": "b"}, "metadata": {}},
            {"task_type": "chapter_to_summary", "input": {"content": "b"}, "output": {"summary": "c"}, "metadata": {}},
        ],
        output_path,
    )

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert count == 2
    assert json.loads(lines[0])["task_type"] == "context_to_chapter"
    assert json.loads(lines[1])["output"]["summary"] == "c"


def test_export_training_data_cli_wrapper_writes_file(client_with_db, tmp_path):
    project = client_with_db.post("/api/projects", json={"idea": "一座灯塔会记录每个失踪者的影子"}).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)
    output_path = tmp_path / "export.jsonl"

    try:
        generate_chapter_candidate(session, project["chapters"][0]["id"])
        accept_chapter_candidate(session, project["chapters"][0]["id"])

        count = export_training_data(session, output_path)
    finally:
        session_generator.close()

    assert count >= 3
    assert output_path.exists()
