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
from app.services.provider_factory import get_model_provider_from_snapshot
from app.services.vector_memory import VectorMemoryDocument, retrieve_vector_memory

NodeFn = Callable[[ChapterGenerationState], ChapterGenerationState]

TOTAL_CONTEXT_BUDGET = 6000
SECTION_BUDGETS = {
    "chapter_summaries": 1600,
    "story_events": 1200,
    "inspirations": 800,
    "foreshadowing_items": 1200,
    "world_rules": 1200,
}


def build_chapter_generation_graph(
    session: Session,
    provider: ModelProvider,
    model_config_snapshot: dict | None = None,
):
    workflow = StateGraph(ChapterGenerationState)
    generation_provider = _provider_for_route(provider, model_config_snapshot, "generation")
    audit_provider = _provider_for_route(provider, model_config_snapshot, "audit")
    summary_provider = _provider_for_route(provider, model_config_snapshot, "summary")

    workflow.add_node("load_context", _persisted_step(session, "load_context", _load_context(session)))
    workflow.add_node("build_chapter_target", _persisted_step(session, "build_chapter_target", _build_chapter_target))
    workflow.add_node("build_prompt_package", _persisted_step(session, "build_prompt_package", _build_prompt_package))
    workflow.add_node(
        "generate_prose",
        _persisted_step(
            session,
            "generate_prose",
            _generate_prose(generation_provider, _route_config_snapshot(model_config_snapshot, "generation")),
        ),
    )
    workflow.add_node(
        "audit_prose",
        _persisted_step(
            session,
            "audit_prose",
            _audit_prose(audit_provider, _route_config_snapshot(model_config_snapshot, "audit")),
        ),
    )
    workflow.add_node(
        "summarize_chapter",
        _persisted_step(
            session,
            "summarize_chapter",
            _summarize_chapter(summary_provider, _route_config_snapshot(model_config_snapshot, "summary")),
        ),
    )
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


def _provider_for_route(provider: ModelProvider, model_config_snapshot: dict | None, route: str) -> ModelProvider:
    if not model_config_snapshot:
        return provider
    return get_model_provider_from_snapshot(model_config_snapshot, route=route)


def _route_config_snapshot(model_config_snapshot: dict | None, route: str) -> dict:
    if not model_config_snapshot:
        return {}
    routes = model_config_snapshot.get("routes")
    if isinstance(routes, dict) and isinstance(routes.get(route), dict):
        return dict(routes[route])
    return {
        key: model_config_snapshot[key]
        for key in ("provider", "base_url", "model", "max_tokens", "api_key_set")
        if key in model_config_snapshot
    }


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
            "generation_model_config",
            "audit_model_config",
            "summary_model_config",
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
        accepted_chapters = [
            item
            for item in sorted(project.chapters, key=lambda chapter_item: chapter_item.number, reverse=True)
            if item.summary and item.status == ChapterStatus.accepted
        ]
        summary_items = [f"第 {item.number} 章：{item.summary}" for item in accepted_chapters]
        inspirations = [item.content for item in reversed(project.inspirations) if not item.applied]
        characters = [
            {
                "name": item.name,
                "role": item.role,
                "current_goal": item.current_goal,
                "key_memories": item.key_memories,
                "relationships": item.relationships,
                "period_stage": item.period_stage,
                "period_summary": item.period_summary,
                "period_source_chapter_id": item.period_source_chapter_id,
            }
            for item in project.characters
        ]
        foreshadowing_candidates = [
            {
                "id": item.id,
                "content": item.content,
                "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                "notes": item.notes,
            }
            for item in project.foreshadowing_items
        ]
        chapters = [{"number": item.number, "title": item.title, "summary": item.summary} for item in project.chapters]
        story_event_candidates = [
            {
                "id": item.id,
                "title": item.title,
                "summary": item.summary,
                "characters": item.characters,
                "location": item.location,
                "consequence": item.consequence,
                "source_chapter_id": item.source_chapter_id,
            }
            for item in sorted(project.story_events, key=lambda event: event.id, reverse=True)
        ]
        world_rule_candidates = [
            {
                "id": item.id,
                "rule": item.rule,
                "limitation": item.limitation,
                "exception": item.exception,
                "status": item.status,
                "source_chapter_id": item.source_chapter_id,
            }
            for item in sorted(project.world_rules, key=lambda rule: rule.id, reverse=True)
        ]
        retrieval_query = _build_retrieval_query(project, chapter, characters, inspirations)
        retrieval_documents = _build_vector_memory_documents(
            project_id=project.id,
            chapters=accepted_chapters,
            characters=characters,
            foreshadowing_items=foreshadowing_candidates,
            world_rules=world_rule_candidates,
            story_events=story_event_candidates,
        )
        candidates = {
            "foreshadowing_items": foreshadowing_candidates,
            "world_rules": world_rule_candidates,
            "chapter_summaries": summary_items,
            "story_events": story_event_candidates,
            "inspirations": inspirations,
        }
        retrieval_results = _retrieve_context(project.id, retrieval_query, retrieval_documents)
        ranked_candidates = _rank_candidates_by_retrieval(candidates, retrieval_results.get("hits", []))
        budgeted = _build_context_budget(ranked_candidates)
        foreshadowing_items = budgeted["included"]["foreshadowing_items"]
        world_rules = budgeted["included"]["world_rules"]
        summaries = budgeted["included"]["chapter_summaries"]
        story_events = budgeted["included"]["story_events"]
        included_inspirations = budgeted["included"]["inspirations"]
        context = "\n".join(
            [
                f"小说定位：{project.positioning or ''}",
                f"世界观：{project.worldview or ''}",
                f"主线：{project.main_plot or ''}",
                f"角色卡：{characters}",
                f"事件时间线：{story_events}",
                f"世界观规则表：{world_rules}",
                f"伏笔：{foreshadowing_items}",
                f"前文摘要：{'；'.join(summaries)}",
                f"作者灵感：{'；'.join(included_inspirations)}",
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
                "story_events": story_events,
                "world_rules": world_rules,
                "chapter_summaries": summaries,
                "inspirations": included_inspirations,
                "chapters": chapters,
                "retrieval_results": retrieval_results,
                "context_budget": budgeted["report"],
            },
        }

    return run


def _build_retrieval_query(project, chapter: Chapter, characters: list[dict], inspirations: list[str]) -> str:
    character_text = "；".join(
        "；".join(
            str(value)
            for value in (
                item.get("name"),
                item.get("role"),
                item.get("current_goal"),
                item.get("key_memories"),
                item.get("relationships"),
                item.get("period_stage"),
                item.get("period_summary"),
            )
            if value
        )
        for item in characters
    )
    return "\n".join(
        item
        for item in (
            chapter.title,
            project.positioning or "",
            project.worldview or "",
            project.main_plot or "",
            character_text,
            "；".join(inspirations),
        )
        if item
    )


def _build_vector_memory_documents(
    project_id: int,
    chapters: list[Chapter],
    characters: list[dict],
    foreshadowing_items: list[dict],
    world_rules: list[dict],
    story_events: list[dict],
) -> list[VectorMemoryDocument]:
    documents: list[VectorMemoryDocument] = []
    documents.extend(
        VectorMemoryDocument(
            source="chapter_summaries",
            source_id=str(chapter.id),
            project_id=project_id,
            text=f"第 {chapter.number} 章：{chapter.summary}",
            metadata={"chapter_number": chapter.number, "title": chapter.title},
        )
        for chapter in chapters
        if chapter.summary
    )
    documents.extend(
        VectorMemoryDocument(
            source="story_events",
            source_id=str(item.get("id") or item.get("source_chapter_id") or index),
            project_id=project_id,
            text=_context_item_text(item),
            metadata={"source_chapter_id": item.get("source_chapter_id")},
        )
        for index, item in enumerate(story_events)
    )
    documents.extend(
        VectorMemoryDocument(
            source="world_rules",
            source_id=str(item.get("id") or item.get("source_chapter_id") or index),
            project_id=project_id,
            text=_context_item_text(item),
            metadata={"source_chapter_id": item.get("source_chapter_id"), "status": item.get("status")},
        )
        for index, item in enumerate(world_rules)
    )
    documents.extend(
        VectorMemoryDocument(
            source="characters",
            source_id=str(item.get("name") or index),
            project_id=project_id,
            text=_context_item_text(item),
            metadata={"name": item.get("name"), "period_stage": item.get("period_stage")},
        )
        for index, item in enumerate(characters)
    )
    documents.extend(
        VectorMemoryDocument(
            source="foreshadowing_items",
            source_id=str(item.get("id") or index),
            project_id=project_id,
            text=_context_item_text(item),
            metadata={"status": item.get("status")},
        )
        for index, item in enumerate(foreshadowing_items)
    )
    return documents


def _retrieve_context(project_id: int, query: str, documents: list[VectorMemoryDocument]) -> dict:
    try:
        return retrieve_vector_memory(project_id, query, documents)
    except Exception as exc:
        return {"backend": "unavailable", "query": query, "hits": [], "error": str(exc)}


def _rank_candidates_by_retrieval(candidates: dict[str, list], hits: list[dict]) -> dict[str, list]:
    hit_order = {str(item.get("text", "")): index for index, item in enumerate(hits)}
    ranked: dict[str, list] = {}
    for section, items in candidates.items():
        ranked[section] = sorted(
            items,
            key=lambda item: (hit_order.get(_context_item_text(item), len(hit_order) + 1), _context_item_text(item)),
        )
    return ranked


def _build_context_budget(candidates: dict[str, list]) -> dict:
    included: dict[str, list] = {}
    omitted: dict[str, list[str]] = {}
    sections: list[dict] = []
    total_used = 0

    for name, items in candidates.items():
        budget = SECTION_BUDGETS.get(name, 1000)
        kept, skipped, used = _fit_items(items, budget)
        included[name] = kept
        omitted[name] = skipped
        total_used += used
        sections.append(
            {
                "name": name,
                "budget": budget,
                "used": used,
                "included_count": len(kept),
                "omitted_count": len(skipped),
            }
        )

    return {
        "included": included,
        "report": {
            "total_budget": TOTAL_CONTEXT_BUDGET,
            "used": min(total_used, TOTAL_CONTEXT_BUDGET),
            "sections": sections,
            "omitted": omitted,
        },
    }


def _fit_items(items: list, budget: int) -> tuple[list, list[str], int]:
    kept = []
    skipped: list[str] = []
    used = 0

    for item in items:
        size = _rough_context_size(item)
        if used + size <= budget or not kept:
            kept.append(item)
            used += size
        else:
            skipped.append(_compact_omitted_item(item))

    return kept, skipped, used


def _rough_context_size(value) -> int:
    return len(_context_item_text(value))


def _compact_omitted_item(value) -> str:
    return _context_item_text(value)[:120]


def _context_item_text(value) -> str:
    if isinstance(value, dict):
        return "；".join(str(item) for item in value.values() if item is not None and str(item).strip())
    return str(value)


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


def _generate_prose(provider: ModelProvider, model_config: dict) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        result = provider.generate_chapter(state["prompt_package"])
        return {
            "generated_content": result.content,
            "draft_summary": result.summary,
            "generation_model_config": model_config,
            "character_updates": result.character_updates,
            "foreshadowing_updates": result.foreshadowing_updates,
        }

    return run


def _audit_prose(provider: ModelProvider, model_config: dict) -> NodeFn:
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
            "audit_model_config": model_config,
        }

    return run


def _summarize_chapter(provider: ModelProvider, model_config: dict) -> NodeFn:
    def run(state: ChapterGenerationState) -> ChapterGenerationState:
        summary = provider.summarize_chapter(state.get("generated_content", ""))
        return {
            "summary": summary,
            "summary_result": {"summary": summary, "source": "post_audit"},
            "summary_model_config": model_config,
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
            (
                f"{item.get('name', '')}：阶段={item.get('period_stage') or '未标注'}；"
                f"目标={item.get('current_goal', '')}；时期摘要={item.get('period_summary') or ''}"
            )
            for item in package.get("characters", [])
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
