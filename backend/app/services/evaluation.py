from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExpectedItem:
    label: str
    aliases: list[str] | None = None


def evaluate_summary_fact_retention(
    summary: str,
    expected_facts: list[ExpectedItem],
    threshold: float = 0.8,
) -> dict[str, Any]:
    detected, missing = _partition_expected_items(summary, expected_facts)
    total = len(expected_facts)
    rate = _round_rate(len(detected), total)
    return {
        "metric": "summary_fact_retention",
        "retained": [item.label for item in detected],
        "missing": [item.label for item in missing],
        "retained_count": len(detected),
        "total_count": total,
        "retention_rate": rate,
        "threshold": threshold,
        "passed": rate >= threshold,
    }


def evaluate_audit_conflict_detection(
    findings: list[dict[str, Any]],
    expected_conflicts: list[ExpectedItem],
    threshold: float = 0.8,
) -> dict[str, Any]:
    text = "；".join(_finding_text(item) for item in findings)
    detected, missed = _partition_expected_items(text, expected_conflicts)
    total = len(expected_conflicts)
    rate = _round_rate(len(detected), total)
    return {
        "metric": "audit_conflict_detection",
        "detected": [item.label for item in detected],
        "missed": [item.label for item in missed],
        "detected_count": len(detected),
        "total_count": total,
        "recall_rate": rate,
        "threshold": threshold,
        "passed": rate >= threshold,
    }


def _partition_expected_items(text: str, expected_items: list[ExpectedItem]) -> tuple[list[ExpectedItem], list[ExpectedItem]]:
    detected: list[ExpectedItem] = []
    missing: list[ExpectedItem] = []
    for item in expected_items:
        if _matches_expected_item(text, item):
            detected.append(item)
        else:
            missing.append(item)
    return detected, missing


def _matches_expected_item(text: str, expected: ExpectedItem) -> bool:
    candidates = [expected.label]
    candidates.extend(expected.aliases or [])
    return any(candidate and candidate in text for candidate in candidates)


def _finding_text(finding: dict[str, Any]) -> str:
    return "；".join(str(value) for value in finding.values() if value is not None)


def _round_rate(count: int, total: int) -> float:
    if total == 0:
        return 1.0
    return round(count / total, 6)
