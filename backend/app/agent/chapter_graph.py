from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agent.state import ChapterGenerationState
from app.models.chapter import Chapter, ChapterStatus
from app.models.generation import GenerationTask, GenerationTaskStatus, GenerationTaskStep, GenerationTaskStepStatus
from app.models.review import ReviewFinding
from app.services.model_provider import ModelProvider

NodeFn = Callable[[ChapterGenerationState], ChapterGenerationState]


def build_chapter_generation_graph(session: Session, provider: ModelProvider):
    workflow = StateGraph(ChapterGenerationState)

    workflow.add_node("load_context", _persisted_step(session, "load_context", _load_context(session)))
    workflow.add_node("build_chapter_target", _persisted_step(session, "build_chapter_target", _build_chapter_target))
    workflow.add_node("build_prompt_package", _persisted_step(session, "build_prompt_package", _build_prompt_package))
    workflow.add_node("generate_prose", _persisted_step(session, "generate_prose", _generate_prose(provider)))
    workflow.add_node("audit_prose", _persisted_step(session, "audit_prose", _audit_prose(provider)))
    workflow.add_node("summarize_chapter", _persisted_step(session, "summarize_chapter", _summarize_chapter(provider)))
    workflow.add_node("judge_foreshadowing", _persisted_step(session, "judge_foreshadowing", _judge_foreshadowing(provider)))
    workflow.add_node(
        "judge_character_period",
        _persisted_step(session, "judge_character_period", _judge_character_period(provider)),
    )
    workflow.add_node(
        "propose_future_plan_updates",
        _persisted_step(session, "propose_future_plan_updates", _propose_future_plan_updates(provider)),
    )
    workflow.add_node("build_candidate_result", _persisted_step(session, "build_candidate_result", _build_candidate_result))
    workflow.add_node(
        "persist_candidate_result",
        _persisted_step(session, "persist_candidate_result", _persist_candidate_result(session)),
    )

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "build_chapter_target")
    workflow.add_edge("build_chapter_target", "build_prompt_package")
    workflow.add_edge("build_prompt_package", "generate_prose")
    workflow.add_edge("generate_prose", "audit_prose")
    workflow.add_edge("audit_prose", "summarize_chapter")
    workflow.add_edge("summarize_chapter", "judge_foreshadowing")
    workflow.add_edge("judge_foreshadowing", "judge_character_period")
    workflow.add_edge("judge_character_period", "propose_future_plan_updates")
    workflow.add_edge("propose_future_plan_updates", "build_candidate_result")
    workflow.add_edge("build_candidate_result", "persist_candidate_result")
    workflow.add_edge("persist_candidate_result", END)
    return workflow.compile()


def _persisted_step(session: Session, name: str, fn: NodeFn) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        task = session.get_one(GenerationTask, state["task_id"])
        step = _get_or_create_step(session, task.id, name)

        if step.status == GenerationTaskStepStatus.completed and step.output_snapshot:
            return dict(step.output_snapshot)

        now = datetime.utcnow()
        task.status = GenerationTaskStatus.running
        task.current_step = name
        task.error_type = None
        task.error_message = None
        step.status = GenerationTaskStepStatus.running
        step.started_at = now
        step.finished_at = None
        step.error_message = None
        step.input_snapshot = _snapshot_state(state)
        session.commit()

        try:
            if state.get("fail_at") == name:
                raise RuntimeError(f"simulated failure at {name}")
            output = fn(state)
        except Exception as exc:
            step.status = GenerationTaskStepStatus.failed
            step.error_message = str(exc)
            step.finished_at = datetime.utcnow()
            task.status = GenerationTaskStatus.failed
            task.error_type = type(exc).__name__
            task.error_message = str(exc)
            session.commit()
            raise

        step.status = GenerationTaskStepStatus.completed
        step.output_snapshot = _snapshot_state(output)
        step.finished_at = datetime.utcnow()
        session.commit()
        return output

    return run


def _get_or_create_step(session: Session, task_id: int, name: str) -> GenerationTaskStep:
    step = (
        session.query(GenerationTaskStep)
        .filter(GenerationTaskStep.task_id == task_id, GenerationTaskStep.name == name)
        .one_or_none()
    )
    if step is None:
        step = GenerationTaskStep(task_id=task_id, name=name)
        session.add(step)
        session.flush()
    return step


def _snapshot_state(state: ChapterGenerationState) -> dict:
    return {
        key: value
        for key, value in state.items()
        if key
        in {
            "task_id",
            "project_id",
            "chapter_id",
            "context",
            "context_package",
            "chapter_target",
            "prompt_package",
            "generated_content",
            "draft_summary",
            "review_findings",
            "audit_result",
            "summary",
            "summary_result",
            "character_updates",
            "foreshadowing_updates",
            "foreshadowing_decisions",
            "character_period_decisions",
            "future_plan_updates",
            "candidate_result",
            "persistence_result",
        }
    }


def _load_context(session: Session) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        chapter = session.get_one(Chapter, state["chapter_id"])
        project = chapter.project
        summaries = [item.summary for item in project.chapters if item.summary]
        inspirations = [item.content for item in project.inspirations if not item.applied]
        characters = [
            {
                "name": item.name,
                "role": item.role,
                "current_goal": item.current_goal,
                "key_memories": item.key_memories,
            }
            for item in project.characters
        ]
        foreshadowing_items = [
            {
                "content": item.content,
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "notes": item.notes,
            }
            for item in project.foreshadowing_items
        ]
        chapters = [{"number": item.number, "title": item.title, "summary": item.summary} for item in project.chapters]
        context = "\n".join(
            [
                f"小说定位：{project.positioning or ''}",
                f"世界观：{project.worldview or ''}",
                f"主线：{project.main_plot or ''}",
                f"角色卡：{characters}",
                f"伏笔：{foreshadowing_items}",
                f"前文摘要：{'；'.join(summaries)}",
                f"作者灵感：{'；'.join(inspirations)}",
            ]
        )
        return {
            "context": context,
            "context_package": {
                "positioning": project.positioning,
                "worldview": project.worldview,
                "main_plot": project.main_plot,
                "characters": characters,
                "foreshadowing_items": foreshadowing_items,
                "chapter_summaries": summaries,
                "inspirations": inspirations,
                "chapters": chapters,
            },
        }

    return run


def _build_chapter_target(state: ChapterGenerationState) -> ChapterGenerationState:
    return {"chapter_target": "推进当前章节目标，保持人设稳定，并在结尾留下后续钩子。"}


def _build_prompt_package(state: ChapterGenerationState) -> ChapterGenerationState:
    prompt_package = "\n".join(
        [
            state.get("context", ""),
            f"本章目标：{state.get('chapter_target', '')}",
            "要求：生成完整单章草稿，避免提前泄露伏笔。",
        ]
    )
    return {"prompt_package": prompt_package}


def _generate_prose(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        result = provider.generate_chapter(state["prompt_package"])
        return {
            "generated_content": result.content,
            "draft_summary": result.summary,
            "character_updates": result.character_updates,
            "foreshadowing_updates": result.foreshadowing_updates,
        }

    return run


def _audit_prose(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        findings = provider.review_chapter(state["generated_content"], state["prompt_package"])
        serialized = [
            {
                "problem_type": finding.problem_type,
                "message": finding.message,
                "suggestion": finding.suggestion,
                "blocking": finding.blocking,
            }
            for finding in findings
        ]
        return {
            "review_findings": serialized,
            "audit_result": {"findings": serialized, "blocking": any(item["blocking"] for item in serialized)},
        }

    return run


def _summarize_chapter(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        summary = provider.summarize_chapter(state.get("generated_content", ""))
        return {
            "summary": summary,
            "summary_result": {"summary": summary, "source": "post_audit"},
        }

    return run


def _judge_foreshadowing(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        package = state.get("context_package", {})
        existing = [str(item.get("content", "")) for item in package.get("foreshadowing_items", [])]
        decisions = provider.judge_foreshadowing(state.get("generated_content", ""), state.get("context", ""), existing)
        return {"foreshadowing_decisions": _normalize_decisions(decisions)}

    return run


def _judge_character_period(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        package = state.get("context_package", {})
        characters = [
            f"{item.get('name', '')}：{item.get('current_goal', '')}" for item in package.get("characters", [])
        ]
        try:
            decisions = provider.judge_character_period(
                state.get("generated_content", ""),
                state.get("context", ""),
                characters,
            )
        except Exception as exc:
            decisions = {
                "updates": [],
                "new_period_cards": [],
                "relationship_changes": [],
                "memory_changes": [],
                "stage_changed": False,
                "skipped": True,
                "error": str(exc),
            }
        return {"character_period_decisions": _normalize_decisions(decisions)}

    return run


def _propose_future_plan_updates(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        package = state.get("context_package", {})
        chapters = [f"第 {item.get('number')} 章：{item.get('title', '')}" for item in package.get("chapters", [])]
        updates = provider.propose_future_plan_updates(state.get("generated_content", ""), state.get("context", ""), chapters)
        return {"future_plan_updates": _normalize_decisions(updates)}

    return run


def _build_candidate_result(state: ChapterGenerationState) -> ChapterGenerationState:
    candidate_result = {
        "generated_content": state.get("generated_content", ""),
        "summary": state.get("summary", ""),
        "audit": state.get("audit_result", {"findings": []}),
        "foreshadowing": state.get("foreshadowing_decisions", {}),
        "character_period": state.get("character_period_decisions", {}),
        "future_plan": state.get("future_plan_updates", {}),
    }
    return {"candidate_result": candidate_result}


def _persist_candidate_result(session: Session) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        task = session.get_one(GenerationTask, state["task_id"])
        chapter = session.get_one(Chapter, state["chapter_id"])
        chapter.generated_content = state.get("generated_content")
        chapter.summary = state.get("summary")
        chapter.status = ChapterStatus.generated

        for finding in state.get("review_findings", []):
            session.add(
                ReviewFinding(
                    chapter_id=chapter.id,
                    task_id=task.id,
                    problem_type=finding["problem_type"],
                    message=finding["message"],
                    suggestion=finding.get("suggestion"),
                    blocking=finding.get("blocking", False),
                )
            )

        task.status = GenerationTaskStatus.completed
        task.current_step = "persist_candidate_result"
        task.error_type = None
        task.error_message = None
        session.commit()
        return {
            "persistence_result": {
                "chapter_id": chapter.id,
                "saved_candidate": bool(chapter.generated_content),
                "saved_summary": bool(chapter.summary),
                "saved_review_findings": len(state.get("review_findings", [])),
                "official_content_committed": False,
            }
        }

    return run


def _normalize_decisions(value: dict) -> dict:
    return {str(key): item for key, item in value.items()}


def persist_generation_result(session: Session, state: ChapterGenerationState) -> None:
    _persist_candidate_result(session)(state)
