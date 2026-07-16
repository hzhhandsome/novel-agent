from app.services.chapter_service import stream_auto_generate_chapters
from app.services.model_provider import MockModelProvider, ReviewFindingDraft


class BlockingReviewProvider(MockModelProvider):
    def review_chapter(self, content: str, prompt_package: str) -> list[ReviewFindingDraft]:
        return [
            ReviewFindingDraft(
                problem_type="blocking_consistency",
                message="本章偏离主线，不能自动采纳。",
                suggestion="重生成本章。",
                blocking=True,
            )
        ]


def test_auto_generate_stream_accepts_requested_chapters(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一座图书馆在每次落雨时多出一本不存在的书"},
    ).json()

    response = client_with_db.post(
        f"/api/projects/{project['id']}/auto-generate/stream",
        json={"chapter_count": 2},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    text = response.text
    assert "event: auto_task" in text
    assert "event: done" in text
    assert '"kind": "auto_chapter_generation"' in text
    assert '"target_count": 2' in text
    assert '"completed_count": 2' in text
    assert '"status": "completed"' in text
    assert '"current_chapter_task"' in text

    refreshed = client_with_db.get(f"/api/projects/{project['id']}").json()
    accepted = [chapter for chapter in refreshed["chapters"] if chapter["status"] == "accepted"]
    assert len(accepted) == 2
    assert all(chapter["content"] for chapter in accepted)
    assert all(chapter["summary"] for chapter in accepted)


def test_auto_generate_pauses_when_audit_is_blocking(client_with_db):
    project = client_with_db.post(
        "/api/projects",
        json={"idea": "一个邮差给梦境投递真实信件"},
    ).json()
    override_session = next(iter(client_with_db.app.dependency_overrides.values()))
    session_generator = override_session()
    session = next(session_generator)

    try:
        snapshots = list(
            stream_auto_generate_chapters(
                session,
                project["id"],
                chapter_count=2,
                provider=BlockingReviewProvider(),
            )
        )
    finally:
        session_generator.close()

    final = snapshots[-1]
    assert final["status"] == "paused"
    assert final["completed_count"] == 0
    assert final["error_type"] == "BlockingAudit"
    assert "不能自动采纳" in final["error_message"]
