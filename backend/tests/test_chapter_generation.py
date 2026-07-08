def test_generate_chapter_records_steps_and_generated_content(client_with_db):
    project = client_with_db.post("/api/projects", json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"}).json()
    chapter_id = project["chapters"][0]["id"]

    response = client_with_db.post(f"/api/chapters/{chapter_id}/generate")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["chapter"]["generated_content"]
    assert [step["name"] for step in body["steps"]] == [
        "load_context",
        "build_chapter_target",
        "build_prompt_package",
        "generate_prose",
        "review_prose",
        "propose_memory_updates",
    ]
