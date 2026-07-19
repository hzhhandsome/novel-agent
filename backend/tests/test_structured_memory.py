def test_project_creation_returns_initial_structured_memory(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"},
    ).json()

    first_character = project["characters"][0]
    assert first_character["period_stage"] == "初始时期"
    assert "理解初始异常" in first_character["period_summary"]
    assert first_character["period_source_chapter_id"] is None

    assert project["world_rules"]
    first_rule = project["world_rules"][0]
    assert first_rule["source_chapter_id"] is None
    assert "异常规则" in first_rule["rule"]

    assert project["story_events"] == []


def test_load_context_includes_structured_memory(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"},
    ).json()
    chapter_id = project["chapters"][0]["id"]

    task = client_with_db.post(f"/api/chapters/{chapter_id}/generate").json()

    load_context = next(step for step in task["steps"] if step["name"] == "load_context")
    context_package = load_context["output_snapshot"]["context_package"]
    first_character = context_package["characters"][0]
    assert first_character["period_stage"] == "初始时期"
    assert first_character["period_summary"]
    assert context_package["world_rules"]
    assert "story_events" in context_package


def test_accepting_chapter_commits_structured_memory(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个邮差给梦境投递真实信件"},
    ).json()
    chapter_id = project["chapters"][0]["id"]

    client_with_db.post(f"/api/chapters/{chapter_id}/generate")
    accepted = client_with_db.post(f"/api/chapters/{chapter_id}/accept")

    assert accepted.status_code == 200
    refreshed = client_with_db.get(f"/api/projects/{project['id']}").json()
    assert refreshed["story_events"]
    event = refreshed["story_events"][0]
    assert event["source_chapter_id"] == chapter_id
    assert event["summary"]

    first_character = refreshed["characters"][0]
    assert "行动者" in first_character["period_summary"]
    assert first_character["period_source_chapter_id"] == chapter_id


def test_accepting_chapter_commits_foreshadowing_memory(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个邮差给梦境投递真实信件"},
    ).json()
    chapter_id = project["chapters"][0]["id"]

    client_with_db.post(f"/api/chapters/{chapter_id}/generate")
    accepted = client_with_db.post(f"/api/chapters/{chapter_id}/accept")

    assert accepted.status_code == 200
    refreshed = client_with_db.get(f"/api/projects/{project['id']}").json()
    foreshadowing_items = refreshed["foreshadowing_items"]
    assert any("尚未解释的细节" in item["content"] for item in foreshadowing_items)
    committed_item = next(item for item in foreshadowing_items if "尚未解释的细节" in item["content"])
    assert committed_item["source_chapter_id"] == chapter_id
    assert committed_item["status"] == "planted"
    assert "未提前泄露" in committed_item["notes"]
