from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.evaluation import ExpectedItem


@dataclass(frozen=True)
class SummaryFactCase:
    name: str
    summary: str
    expected_facts: list[ExpectedItem]
    threshold: float = 0.8


@dataclass(frozen=True)
class AuditConflictCase:
    name: str
    findings: list[dict[str, Any]]
    expected_conflicts: list[ExpectedItem]
    threshold: float = 0.8


SUMMARY_FACT_CASES = [
    SummaryFactCase(
        name="memory_cost_summary",
        summary="主角在废城图书馆发现手背页码，确认修书会改变现实并付出记忆代价。",
        expected_facts=[
            ExpectedItem(label="废城图书馆"),
            ExpectedItem(label="手背页码"),
            ExpectedItem(label="改变现实"),
            ExpectedItem(label="记忆代价", aliases=["付出记忆"]),
        ],
        threshold=0.75,
    ),
    SummaryFactCase(
        name="foreshadowing_summary",
        summary="红封书页留下未知批注，关键同伴隐瞒了曾经修书的经历。",
        expected_facts=[
            ExpectedItem(label="红封书页"),
            ExpectedItem(label="未知批注"),
            ExpectedItem(label="关键同伴"),
            ExpectedItem(label="曾经修书", aliases=["修书的经历"]),
        ],
        threshold=0.75,
    ),
]


AUDIT_CONFLICT_CASES = [
    AuditConflictCase(
        name="world_rule_memory_cost_conflict",
        findings=[
            {
                "problem_type": "world_rule_conflict",
                "message": "世界观冲突：本章让主角无代价修书，违反记忆代价规则。",
                "blocking": True,
            }
        ],
        expected_conflicts=[
            ExpectedItem(label="世界观冲突"),
            ExpectedItem(label="记忆代价", aliases=["无代价修书"]),
        ],
        threshold=1.0,
    ),
    AuditConflictCase(
        name="foreshadowing_leak_conflict",
        findings=[
            {
                "problem_type": "foreshadowing_leak",
                "message": "伏笔提前泄露：关键同伴直接解释红封书来源。",
                "blocking": True,
            }
        ],
        expected_conflicts=[
            ExpectedItem(label="伏笔提前泄露", aliases=["提前泄露"]),
            ExpectedItem(label="红封书来源"),
        ],
        threshold=1.0,
    ),
]
