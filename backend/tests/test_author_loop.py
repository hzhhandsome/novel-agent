def test_accept_chapter_updates_content_summary_and_future_context(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一个邮差给梦境投递真实信件"}).json()
    chapter_id = project["chapters"][0]["id"]
    client_with_db.post(f"/api/chapters/{chapter_id}/generate")

    accepted = client_with_db.post(f"/api/chapters/{chapter_id}/accept").json()
    inspiration = client_with_db.post(
        f"/api/projects/{project['id']}/inspirations",
        json={"content": "后续必须出现一封写给反派童年的信"},
    ).json()

    assert accepted["status"] == "accepted"
    assert accepted["content"]
    assert accepted["summary"]
    assert inspiration["applied"] is False
