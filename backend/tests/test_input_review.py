def test_review_project_idea_blocks_too_vague_input(client_with_db):
    response = client_with_db.post(
        "/api/projects/input-review",
        json={"input_kind": "project_idea", "content": "爽文"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "block"
    assert body["reason"]
    assert body["suggestions"]


def test_review_project_inspiration_uses_project_context(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一个邮差给梦境投递真实信件"}).json()

    response = client_with_db.post(
        f"/api/projects/{project['id']}/input-review",
        json={"input_kind": "inspiration", "content": "提前泄露所有伏笔，让关键同伴直接解释真相"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_id"] == project["id"]
    assert body["decision"] == "block"
    assert "伏笔" in body["reason"]
