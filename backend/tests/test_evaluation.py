from app.services.evaluation import (
    ExpectedItem,
    evaluate_audit_conflict_detection,
    evaluate_summary_fact_retention,
)


def test_summary_fact_retention_reports_missing_facts():
    result = evaluate_summary_fact_retention(
        summary="主角在废城图书馆发现手背页码，并确认修书会改变现实。",
        expected_facts=[
            ExpectedItem(label="废城图书馆"),
            ExpectedItem(label="手背页码"),
            ExpectedItem(label="失去一段记忆", aliases=["记忆代价"]),
        ],
        threshold=0.8,
    )

    assert result["metric"] == "summary_fact_retention"
    assert result["retained_count"] == 2
    assert result["total_count"] == 3
    assert result["retention_rate"] == 0.666667
    assert result["passed"] is False
    assert result["missing"] == ["失去一段记忆"]


def test_audit_conflict_detection_reports_missed_conflicts():
    result = evaluate_audit_conflict_detection(
        findings=[
            {"message": "世界观冲突：修书没有付出记忆代价。"},
            {"message": "角色动机略显模糊。"},
        ],
        expected_conflicts=[
            ExpectedItem(label="记忆代价", aliases=["付出记忆"]),
            ExpectedItem(label="提前泄露伏笔"),
        ],
        threshold=1.0,
    )

    assert result["metric"] == "audit_conflict_detection"
    assert result["detected_count"] == 1
    assert result["total_count"] == 2
    assert result["recall_rate"] == 0.5
    assert result["passed"] is False
    assert result["missed"] == ["提前泄露伏笔"]


def test_builtin_eval_runner_returns_aggregate_metrics():
    from app.evals.run import run_builtin_evals

    report = run_builtin_evals()

    assert report["summary"]["case_count"] >= 1
    assert report["summary"]["average_retention_rate"] > 0
    assert report["audit"]["case_count"] >= 1
    assert report["audit"]["average_recall_rate"] > 0
    assert report["overall"]["case_count"] == report["summary"]["case_count"] + report["audit"]["case_count"]


def test_builtin_eval_api_returns_report(client_with_db):
    response = client_with_db.get("/api/evals/builtin")

    assert response.status_code == 200
    report = response.json()
    assert report["summary"]["case_count"] >= 1
    assert report["audit"]["case_count"] >= 1
    assert report["overall"]["case_count"] == report["summary"]["case_count"] + report["audit"]["case_count"]
