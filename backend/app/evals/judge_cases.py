from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeEvalCase:
    case_id: str
    name: str
    input_text: str
    context: str
    rubric: str
    threshold: float = 0.75


JUDGE_EVAL_CASES = [
    JudgeEvalCase(
        case_id="chapter_consistency_clean",
        name="章节一致性可用样例",
        input_text=(
            "林辰发现修复红封书会改变现实，但会丢失一段私人记忆。"
            "他没有直接解释红封书来源，只决定继续追查下一条批注。"
        ),
        context="主角林辰正在调查红封书规则；核心限制是每次修书都会付出记忆代价；红封书来源仍是未回收伏笔。",
        rubric=(
            "按 0-1 分评估：consistency 检查是否符合世界观规则；character 检查主角动机是否稳定；"
            "foreshadowing 检查是否提前泄露伏笔；style 检查是否适合悬疑克制文风。"
            "如存在会阻塞采纳的严重问题，写入 blocking_findings。"
        ),
        threshold=0.75,
    )
]
