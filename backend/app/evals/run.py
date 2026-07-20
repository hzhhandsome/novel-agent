from __future__ import annotations

import json
from typing import Any

from app.evals.gold_cases import AUDIT_CONFLICT_CASES, SUMMARY_FACT_CASES
from app.evals.rag_cases import RAG_RETRIEVAL_CASES
from app.services.evaluation import (
    evaluate_audit_conflict_detection,
    evaluate_rag_retrieval,
    evaluate_summary_fact_retention,
)
from app.services.prompt_versions import PROMPT_TEMPLATE_VERSIONS


def run_builtin_evals() -> dict[str, Any]:
    summary_results = [
        {
            "case": case.name,
            "prompt_version": PROMPT_TEMPLATE_VERSIONS["builtin_eval"],
            **evaluate_summary_fact_retention(case.summary, case.expected_facts, threshold=case.threshold),
        }
        for case in SUMMARY_FACT_CASES
    ]
    audit_results = [
        {
            "case": case.name,
            "prompt_version": PROMPT_TEMPLATE_VERSIONS["builtin_eval"],
            **evaluate_audit_conflict_detection(case.findings, case.expected_conflicts, threshold=case.threshold),
        }
        for case in AUDIT_CONFLICT_CASES
    ]
    rag_results = [
        {
            "case": case.name,
            "prompt_version": PROMPT_TEMPLATE_VERSIONS["builtin_eval"],
            **evaluate_rag_retrieval(
                case.retrieval_report,
                case.expected_documents,
                top_k=case.top_k,
                threshold=case.threshold,
            ),
        }
        for case in RAG_RETRIEVAL_CASES
    ]
    return {
        "summary": {
            "case_count": len(summary_results),
            "average_retention_rate": _average(item["retention_rate"] for item in summary_results),
            "passed_count": sum(1 for item in summary_results if item["passed"]),
            "cases": summary_results,
        },
        "audit": {
            "case_count": len(audit_results),
            "average_recall_rate": _average(item["recall_rate"] for item in audit_results),
            "passed_count": sum(1 for item in audit_results if item["passed"]),
            "cases": audit_results,
        },
        "rag": {
            "case_count": len(rag_results),
            "average_recall_at_k": _average(item["recall_at_k"] for item in rag_results),
            "average_precision_at_k": _average(item["precision_at_k"] for item in rag_results),
            "average_hit_rate_at_k": _average(item["hit_rate_at_k"] for item in rag_results),
            "average_mrr": _average(item["mrr"] for item in rag_results),
            "passed_count": sum(1 for item in rag_results if item["passed"]),
            "cases": rag_results,
        },
        "overall": {
            "case_count": len(summary_results) + len(audit_results) + len(rag_results),
            "passed_count": sum(1 for item in summary_results + audit_results + rag_results if item["passed"]),
        },
        "prompt_versions": _prompt_version_groups(summary_results + audit_results + rag_results),
    }


def main() -> None:
    print(json.dumps(run_builtin_evals(), ensure_ascii=False, indent=2))


def _average(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 6)


def _prompt_version_groups(results: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    for item in results:
        version = str(item.get("prompt_version") or "unknown")
        group = groups.setdefault(version, {"prompt_version": version, "case_count": 0, "passed_count": 0})
        group["case_count"] += 1
        if item.get("passed"):
            group["passed_count"] += 1
    return {
        "case_count": len(results),
        "groups": list(groups.values()),
    }


if __name__ == "__main__":
    main()
