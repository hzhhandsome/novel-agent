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
    workflow.add_node("review_prose", _persisted_step(session, "review_prose", _review_prose(provider)))
    workflow.add_node("propose_memory_updates", _persisted_step(session, "propose_memory_updates", _propose_memory_updates(provider)))

    workflow.set_entry_point("load_context")
    workflow.add_edge("load_context", "build_chapter_target")
    workflow.add_edge("build_chapter_target", "build_prompt_package")
    workflow.add_edge("build_prompt_package", "generate_prose")
    workflow.add_edge("generate_prose", "review_prose")
    workflow.add_edge("review_prose", "propose_memory_updates")
    workflow.add_edge("propose_memory_updates", END)
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
            "chapter_target",
            "prompt_package",
            "generated_content",
            "review_findings",
            "summary",
            "character_updates",
            "foreshadowing_updates",
        }
    }


def _load_context(session: Session) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        chapter = session.get_one(Chapter, state["chapter_id"])
        project = chapter.project
        summaries = [item.summary for item in project.chapters if item.summary]
        inspirations = [item.content for item in project.inspirations if not item.applied]
        context = "\n".join(
            [
                f"小说定位：{project.positioning or ''}",
                f"世界观：{project.worldview or ''}",
                f"主线：{project.main_plot or ''}",
                f"前文摘要：{'；'.join(summaries)}",
                f"作者灵感：{'；'.join(inspirations)}",
            ]
        )
        return {"context": context}

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
            "summary": result.summary,
            "character_updates": result.character_updates,
            "foreshadowing_updates": result.foreshadowing_updates,
        }

    return run


def _review_prose(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        findings = provider.review_chapter(state["generated_content"], state["prompt_package"])
        return {
            "review_findings": [
                {
                    "problem_type": finding.problem_type,
                    "message": finding.message,
                    "suggestion": finding.suggestion,
                    "blocking": finding.blocking,
                }
                for finding in findings
            ]
        }

    return run


def _propose_memory_updates(provider: ModelProvider) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        return {
            "summary": state.get("summary") or provider.summarize_chapter(state.get("generated_content", "")),
            "character_updates": state.get("character_updates", []),
            "foreshadowing_updates": state.get("foreshadowing_updates", []),
        }

    return run


def persist_generation_result(session: Session, state: ChapterGenerationState) -> None:
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
    task.current_step = "propose_memory_updates"
    task.error_type = None
    task.error_message = None
    session.commit()
