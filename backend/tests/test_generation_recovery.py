def test_failed_generation_can_be_retried_from_persisted_task(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一名钟表师能听见城市未来一分钟的声音"}).json()
    chapter_id = project["chapters"][0]["id"]

    failed = client_with_db.post(f"/api/chapters/{chapter_id}/generate", json={"fail_at": "audit_prose"}).json()
    retry = client_with_db.post(f"/api/generation-tasks/{failed['id']}/retry")

    assert retry.status_code == 200
    assert retry.json()["status"] == "completed"
