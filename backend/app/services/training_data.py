from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.generation import GenerationRun, GenerationTask


def export_training_examples(session: Session, include_rejected: bool = False) -> list[dict[str, Any]]:
    statement = (
        select(GenerationRun)
        .join(GenerationRun.task)
        .options(selectinload(GenerationRun.task).selectinload(GenerationTask.chapter))
        .order_by(GenerationRun.id)
    )
    if not include_rejected:
        statement = statement.where(GenerationRun.accepted.is_(True))

    examples: list[dict[str, Any]] = []
    for run in session.scalars(statement).all():
        examples.extend(_examples_for_run(run))
    return [_sanitize(example) for example in examples]


def write_training_jsonl(examples: Iterable[dict[str, Any]], output_path: str | Path) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as file:
        for example in examples:
            file.write(json.dumps(_sanitize(example), ensure_ascii=False, sort_keys=True))
            file.write("\n")
            count += 1
    return count


def _examples_for_run(run: GenerationRun) -> list[dict[str, Any]]:
    chapter = run.task.chapter if run.task else None
    metadata = {
        "project_id": run.task.project_id if run.task else None,
        "chapter_id": run.task.chapter_id if run.task else None,
        "chapter_number": chapter.number if chapter else None,
        "generation_run_id": run.id,
        "generation_task_id": run.task_id,
        "accepted": bool(run.accepted),
        "model_config_snapshot": run.model_config_snapshot,
        "model_usage_snapshot": run.model_usage_snapshot,
    }
    examples = []
    if run.prompt_package and run.output_text:
        examples.append(
            _example(
                "context_to_chapter",
                {"prompt_package": run.prompt_package},
                {"content": run.output_text},
                metadata,
            )
        )
    if run.output_text and chapter and chapter.summary:
        examples.append(
            _example(
                "chapter_to_summary",
                {"content": run.output_text},
                {"summary": chapter.summary},
                metadata,
            )
        )
    if run.prompt_package and run.output_text and run.review_result is not None:
        examples.append(
            _example(
                "chapter_to_audit",
                {"prompt_package": run.prompt_package, "content": run.output_text},
                {"review_result": run.review_result},
                metadata,
            )
        )
    return examples


def _example(task_type: str, input_value: dict, output_value: dict, metadata: dict) -> dict[str, Any]:
    return {
        "task_type": task_type,
        "input": input_value,
        "output": output_value,
        "metadata": metadata,
    }


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize(item) for key, item in value.items() if "api_key" not in key}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value
