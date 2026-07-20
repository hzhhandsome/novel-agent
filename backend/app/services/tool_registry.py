from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.models.foreshadowing import ForeshadowingItem, ForeshadowingStatus


class ToolCallValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required: tuple[str, ...]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self, specs: dict[str, ToolSpec]) -> None:
        self._specs = specs

    def call(self, tool_name: str, arguments: dict[str, Any], task_id: int | None, step_name: str) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            spec = self._specs[tool_name]
            self._validate(spec, arguments)
            result = spec.handler(arguments)
            return _record(
                tool_name=tool_name,
                arguments=arguments,
                task_id=task_id,
                step_name=step_name,
                status="completed",
                result=result,
                error_type="",
                error="",
                started=started,
            )
        except Exception as exc:
            return _record(
                tool_name=tool_name,
                arguments=arguments,
                task_id=task_id,
                step_name=step_name,
                status="failed",
                result={},
                error_type=type(exc).__name__,
                error=str(exc),
                started=started,
            )

    def _validate(self, spec: ToolSpec, arguments: dict[str, Any]) -> None:
        for key in spec.required:
            if arguments.get(key) in (None, ""):
                raise ToolCallValidationError(f"missing required argument: {key}")


def get_internal_tool_registry(session: Session) -> ToolRegistry:
    def list_open_foreshadowing(arguments: dict[str, Any]) -> dict[str, Any]:
        project_id = int(arguments["project_id"])
        items = [
            {
                "id": item.id,
                "content": item.content,
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "notes": item.notes,
            }
            for item in session.query(ForeshadowingItem)
            .filter(ForeshadowingItem.project_id == project_id)
            .order_by(ForeshadowingItem.id.asc())
            .all()
            if item.status != ForeshadowingStatus.recovered
        ]
        return {"items": items, "count": len(items)}

    def get_chapter_summary(arguments: dict[str, Any]) -> dict[str, Any]:
        chapter = session.get_one(Chapter, int(arguments["chapter_id"]))
        return {
            "chapter_id": chapter.id,
            "project_id": chapter.project_id,
            "number": chapter.number,
            "title": chapter.title,
            "summary": chapter.summary,
        }

    return ToolRegistry(
        {
            "list_open_foreshadowing": ToolSpec(
                name="list_open_foreshadowing",
                description="Read open foreshadowing items for a project.",
                required=("project_id",),
                handler=list_open_foreshadowing,
            ),
            "get_chapter_summary": ToolSpec(
                name="get_chapter_summary",
                description="Read a chapter summary.",
                required=("chapter_id",),
                handler=get_chapter_summary,
            ),
        }
    )


def _record(
    tool_name: str,
    arguments: dict[str, Any],
    task_id: int | None,
    step_name: str,
    status: str,
    result: dict[str, Any],
    error_type: str,
    error: str,
    started: float,
) -> dict[str, Any]:
    return {
        "tool_name": tool_name,
        "task_id": task_id,
        "step_name": step_name,
        "arguments": dict(arguments),
        "status": status,
        "result": result,
        "result_summary": _summarize_result(result),
        "error_type": error_type,
        "error": error,
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }


def _summarize_result(result: dict[str, Any]) -> str:
    if "items" in result and isinstance(result["items"], list):
        return f"items={len(result['items'])}"
    if "summary" in result:
        summary = str(result.get("summary") or "")
        return summary[:120] if summary else "summary=empty"
    return ", ".join(f"{key}={value}" for key, value in result.items() if key != "items")[:120]
