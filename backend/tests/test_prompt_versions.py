from app.services.prompt_versions import CONTEXT_BUILDER_VERSION, prompt_metadata


def test_prompt_metadata_uses_stable_version_and_hash():
    first = prompt_metadata("generate_prose", "写一章正文")
    second = prompt_metadata("generate_prose", "写一章正文")

    assert first["prompt_template"] == "generate_prose"
    assert first["prompt_version"] == "generate_prose@2026-07-20.v1"
    assert first["context_builder_version"] == CONTEXT_BUILDER_VERSION
    assert first["prompt_hash"] == second["prompt_hash"]
    assert len(first["prompt_hash"]) == 64


def test_builtin_eval_report_groups_results_by_prompt_version():
    from app.evals.run import run_builtin_evals

    report = run_builtin_evals()

    assert report["prompt_versions"]["case_count"] == report["overall"]["case_count"]
    assert report["prompt_versions"]["groups"]
    group = report["prompt_versions"]["groups"][0]
    assert group["prompt_version"] == "builtin_eval@2026-07-20.v1"
    assert group["case_count"] == report["overall"]["case_count"]
    assert group["passed_count"] == report["overall"]["passed_count"]
