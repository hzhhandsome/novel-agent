from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.generation import GenerationTask, GenerationTaskStep


def build_task_trace(task: GenerationTask) -> dict[str, Any]:
    root_span_id = f"task-{task.id}"
    events = [_task_event(task, root_span_id)]
    for step in task.steps:
        step_span_id = f"step-{step.id}"
        events.append(_step_event(step, root_span_id, step_span_id))
        events.extend(_child_events(step, step_span_id))
    return {
        "trace_id": f"generation-task-{task.id}",
        "root_span_id": root_span_id,
        "events": events,
    }


def _task_event(task: GenerationTask, span_id: str) -> dict[str, Any]:
    metadata = {
        "task_id": task.id,
        "project_id": task.project_id,
        "chapter_id": task.chapter_id,
        "current_step": task.current_step,
        "error_type": task.error_type,
        "error_message": task.error_message,
    }
    return _event(
        span_id=span_id,
        parent_span_id=None,
        event_type="task",
        name=task.kind,
        status=_value(task.status),
        summary=_summary_status("task", _value(task.status), task.error_message),
        duration_ms=_duration_between(task.created_at, task.updated_at),
        metadata=metadata,
    )


def _step_event(step: GenerationTaskStep, parent_span_id: str, span_id: str) -> dict[str, Any]:
    metadata = {
        "step_id": step.id,
        "task_id": step.task_id,
        "error_message": step.error_message,
    }
    return _event(
        span_id=span_id,
        parent_span_id=parent_span_id,
        event_type="step",
        name=step.name,
        status=_value(step.status),
        summary=_summary_status(step.name, _value(step.status), step.error_message),
        duration_ms=_duration_between(step.started_at, step.finished_at),
        metadata=metadata,
    )


def _child_events(step: GenerationTaskStep, parent_span_id: str) -> list[dict[str, Any]]:
    output = step.output_snapshot if isinstance(step.output_snapshot, dict) else {}
    events: list[dict[str, Any]] = []
    events.extend(_llm_events(step, parent_span_id, output))
    retrieval = _nested(output, "context_package").get("retrieval_results")
    if isinstance(retrieval, dict):
        events.append(_retrieval_event(step, parent_span_id, retrieval))
    for index, call in enumerate(output.get("tool_calls") if isinstance(output.get("tool_calls"), list) else []):
        if isinstance(call, dict):
            events.append(_tool_event(step, parent_span_id, index, call))
    persistence = output.get("persistence_result")
    if isinstance(persistence, dict):
        events.append(_persistence_event(step, parent_span_id, persistence))
    return events


def _llm_events(step: GenerationTaskStep, parent_span_id: str, output: dict[str, Any]) -> list[dict[str, Any]]:
    events = []
    for key, usage in output.items():
        if not key.endswith("_model_usage") or not isinstance(usage, dict):
            continue
        node = str(usage.get("node") or key.removesuffix("_model_usage"))
        input_tokens = int(usage.get("estimated_input_tokens") or 0)
        output_tokens = int(usage.get("estimated_output_tokens") or 0)
        events.append(
            _event(
                span_id=f"{parent_span_id}-llm-{node}",
                parent_span_id=parent_span_id,
                event_type="llm_call",
                name=node,
                status="completed",
                summary=f"{node}: {input_tokens + output_tokens} estimated tokens",
                duration_ms=_int_or_none(usage.get("duration_ms")),
                metadata=dict(usage),
            )
        )
    return events


def _retrieval_event(step: GenerationTaskStep, parent_span_id: str, retrieval: dict[str, Any]) -> dict[str, Any]:
    hits = retrieval.get("hits") if isinstance(retrieval.get("hits"), list) else []
    metadata = {
        "backend": retrieval.get("backend"),
        "query": retrieval.get("query"),
        "hit_count": len(hits),
        "error": retrieval.get("error"),
    }
    return _event(
        span_id=f"{parent_span_id}-retrieval",
        parent_span_id=parent_span_id,
        event_type="retrieval",
        name="RAG retrieval",
        status="failed" if retrieval.get("error") else "completed",
        summary=f"{metadata['backend'] or 'retrieval'}: {len(hits)} hits",
        duration_ms=None,
        metadata=metadata,
    )


def _tool_event(step: GenerationTaskStep, parent_span_id: str, index: int, call: dict[str, Any]) -> dict[str, Any]:
    name = str(call.get("tool_name") or f"tool_{index}")
    return _event(
        span_id=f"{parent_span_id}-tool-{index}",
        parent_span_id=parent_span_id,
        event_type="tool_call",
        name=name,
        status=str(call.get("status") or "unknown"),
        summary=str(call.get("result_summary") or call.get("error") or name),
        duration_ms=_int_or_none(call.get("duration_ms")),
        metadata=dict(call),
    )


def _persistence_event(step: GenerationTaskStep, parent_span_id: str, persistence: dict[str, Any]) -> dict[str, Any]:
    saved = [
        key
        for key in ("saved_candidate", "saved_summary", "official_content_committed")
        if persistence.get(key) is True
    ]
    return _event(
        span_id=f"{parent_span_id}-persistence",
        parent_span_id=parent_span_id,
        event_type="persistence",
        name="persist_candidate_result",
        status="completed",
        summary=", ".join(saved) if saved else "persistence recorded",
        duration_ms=None,
        metadata=dict(persistence),
    )


def _event(
    span_id: str,
    parent_span_id: str | None,
    event_type: str,
    name: str,
    status: str,
    summary: str,
    duration_ms: int | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "event_type": event_type,
        "name": name,
        "status": status,
        "summary": summary,
        "duration_ms": duration_ms,
        "metadata": metadata,
    }


def _nested(source: dict[str, Any], key: str) -> dict[str, Any]:
    value = source.get(key)
    return value if isinstance(value, dict) else {}


def _summary_status(name: str, status: str, error_message: str | None) -> str:
    if error_message:
        return f"{name}: {error_message}"
    return f"{name} {status}"


def _duration_between(started: datetime | None, finished: datetime | None) -> int | None:
    if not started or not finished:
        return None
    return max(0, round((finished - started).total_seconds() * 1000))


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)
