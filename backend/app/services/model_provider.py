from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Protocol
from urllib import request


@dataclass(frozen=True)
class CharacterDraft:
    name: str
    role: str
    personality: str
    current_goal: str
    key_memories: str
    relationships: str
    writing_notes: str


@dataclass(frozen=True)
class ChapterPlanDraft:
    number: int
    title: str


@dataclass(frozen=True)
class ProjectSetupResult:
    title: str
    positioning: str
    worldview: str
    main_plot: str
    characters: list[CharacterDraft]
    chapters: list[ChapterPlanDraft]


@dataclass(frozen=True)
class ReviewFindingDraft:
    problem_type: str
    message: str
    suggestion: str
    blocking: bool = False


@dataclass(frozen=True)
class MemoryUpdateDraft:
    summary: str
    character_updates: list[str]
    foreshadowing_updates: list[str]


@dataclass(frozen=True)
class ChapterGenerationResult:
    content: str
    summary: str
    character_updates: list[str]
    foreshadowing_updates: list[str]


@dataclass(frozen=True)
class UserInputReviewResult:
    decision: str
    reason: str
    suggestions: list[str]


class ModelProvider(Protocol):
    def generate_project_setup(self, idea: str) -> ProjectSetupResult:
        raise NotImplementedError

    def generate_chapter(self, prompt_package: str) -> ChapterGenerationResult:
        raise NotImplementedError

    def review_chapter(self, content: str, prompt_package: str) -> list[ReviewFindingDraft]:
        raise NotImplementedError

    def summarize_chapter(self, content: str) -> str:
        raise NotImplementedError

    def judge_foreshadowing(self, content: str, context: str, existing_items: list[str]) -> dict[str, Any]:
        raise NotImplementedError

    def judge_character_period(self, content: str, context: str, characters: list[str]) -> dict[str, Any]:
        raise NotImplementedError

    def propose_future_plan_updates(self, content: str, context: str, chapters: list[str]) -> dict[str, Any]:
        raise NotImplementedError

    def review_user_input(self, input_kind: str, content: str, context: str) -> UserInputReviewResult:
        raise NotImplementedError


Transport = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


class DeepSeekAnthropicProvider:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        max_tokens: int = 4096,
        transport: Transport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("DeepSeek API key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.transport = transport or self._default_transport

    def generate_project_setup(self, idea: str) -> ProjectSetupResult:
        payload = self._call_json(
            system="你是小说策划助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "基于这个小说想法生成项目设定。JSON 字段必须包含："
                "title, positioning, worldview, main_plot, characters, chapters。"
                "characters 每项包含 name, role, personality, current_goal, key_memories, relationships, writing_notes。"
                "chapters 每项包含 number, title。"
                f"\n小说想法：{idea}"
            ),
        )
        return ProjectSetupResult(
            title=str(payload["title"]),
            positioning=str(payload["positioning"]),
            worldview=str(payload["worldview"]),
            main_plot=str(payload["main_plot"]),
            characters=[
                CharacterDraft(
                    name=str(item["name"]),
                    role=str(item["role"]),
                    personality=str(item["personality"]),
                    current_goal=str(item["current_goal"]),
                    key_memories=str(item["key_memories"]),
                    relationships=str(item["relationships"]),
                    writing_notes=str(item["writing_notes"]),
                )
                for item in payload["characters"]
            ],
            chapters=[
                ChapterPlanDraft(number=int(item["number"]), title=str(item["title"]))
                for item in payload["chapters"]
            ],
        )

    def generate_chapter(self, prompt_package: str) -> ChapterGenerationResult:
        payload = self._call_json(
            system="你是小说章节写作助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "根据提示包生成章节候选稿。JSON 字段必须包含："
                "content, summary, character_updates, foreshadowing_updates。"
                f"\n提示包：{prompt_package}"
            ),
        )
        return ChapterGenerationResult(
            content=str(payload["content"]),
            summary=str(payload["summary"]),
            character_updates=[str(item) for item in payload.get("character_updates", [])],
            foreshadowing_updates=[str(item) for item in payload.get("foreshadowing_updates", [])],
        )

    def review_chapter(self, content: str, prompt_package: str) -> list[ReviewFindingDraft]:
        payload = self._call_json(
            system="你是小说章节审核助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "审核章节是否有连贯性、设定冲突和节奏问题。"
                "JSON 字段必须包含 findings 数组，每项包含 problem_type, message, suggestion, blocking。"
                f"\n提示包：{prompt_package}\n章节正文：{content}"
            ),
        )
        return [
            ReviewFindingDraft(
                problem_type=str(item["problem_type"]),
                message=str(item["message"]),
                suggestion=str(item["suggestion"]),
                blocking=bool(item.get("blocking", False)),
            )
            for item in payload.get("findings", [])
        ]

    def summarize_chapter(self, content: str) -> str:
        payload = self._call_json(
            system="你是小说章节摘要助手。只输出合法 JSON，不要输出 Markdown。",
            user=f"为下面章节写一句可供后续章节引用的摘要。JSON 字段必须包含 summary。\n章节正文：{content}",
        )
        return str(payload["summary"])

    def judge_foreshadowing(self, content: str, context: str, existing_items: list[str]) -> dict[str, Any]:
        return self._call_json(
            system="你是小说伏笔管理助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "判断章节中的伏笔变化。JSON 字段必须包含 new, advanced, resolved, leaked, notes。"
                f"\n上下文：{context}\n已有伏笔：{existing_items}\n章节正文：{content}"
            ),
        )

    def judge_character_period(self, content: str, context: str, characters: list[str]) -> dict[str, Any]:
        return self._call_json(
            system="你是小说角色状态管理助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "判断角色时期卡变化。JSON 字段必须包含 updates, new_period_cards, "
                "relationship_changes, memory_changes, stage_changed。"
                f"\n上下文：{context}\n角色：{characters}\n章节正文：{content}"
            ),
        )

    def propose_future_plan_updates(self, content: str, context: str, chapters: list[str]) -> dict[str, Any]:
        return self._call_json(
            system="你是小说章节规划助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "根据本章实际正文判断后续章节标题和线路是否需要调整。"
                "JSON 字段必须包含 suggestions 数组和 notes。"
                f"\n上下文：{context}\n后续章节：{chapters}\n章节正文：{content}"
            ),
        )

    def review_user_input(self, input_kind: str, content: str, context: str) -> UserInputReviewResult:
        payload = self._call_json(
            system="你是小说创作输入审核助手。只输出合法 JSON，不要输出 Markdown。",
            user=(
                "判断用户输入是否适合进入小说项目上下文。"
                "JSON 字段必须包含 decision, reason, suggestions。"
                "decision 只能是 pass, warning, block。"
                "重点检查：世界观冲突、人设动机破坏、前文摘要矛盾、伏笔提前泄露、过于模糊。"
                f"\n输入类型：{input_kind}\n项目上下文：{context}\n用户输入：{content}"
            ),
        )
        decision = str(payload.get("decision", "warning"))
        if decision not in {"pass", "warning", "block"}:
            decision = "warning"
        return UserInputReviewResult(
            decision=decision,
            reason=str(payload.get("reason", "")),
            suggestions=[str(item) for item in payload.get("suggestions", [])],
        )

    def _call_json(self, system: str, user: str) -> dict[str, Any]:
        response = self.transport(
            f"{self.base_url}/v1/messages",
            {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
        text = self._extract_text(response)
        return self._parse_json_object(text)

    @staticmethod
    def _extract_text(response: dict[str, Any]) -> str:
        content = response.get("content", [])
        if isinstance(content, list):
            return "\n".join(str(item.get("text", "")) for item in content if isinstance(item, dict)).strip()
        return str(content)

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("model response did not contain a JSON object")
        parsed = json.loads(stripped[start : end + 1])
        if not isinstance(parsed, dict):
            raise ValueError("model response JSON must be an object")
        return parsed

    @staticmethod
    def _default_transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method="POST")
        with request.urlopen(req, timeout=90) as response:
            body = response.read().decode("utf-8")
        parsed = json.loads(body)
        if not isinstance(parsed, dict):
            raise ValueError("model API response must be a JSON object")
        return parsed


class MockModelProvider:
    def generate_project_setup(self, idea: str) -> ProjectSetupResult:
        short_idea = idea.strip()
        title = short_idea if len(short_idea) <= 18 else f"{short_idea[:18]}..."
        return ProjectSetupResult(
            title=title,
            positioning=f"以“{short_idea}”为核心卖点的自动化长篇小说，偏重悬念、人物选择和连续推进。",
            worldview=f"故事世界围绕“{short_idea}”建立一条清晰异常规则，并通过章节逐步展示代价。",
            main_plot="主角从被动卷入开始，逐步掌握规则、承担代价，并在关键选择中改变结局。",
            characters=[
                CharacterDraft(
                    name="主角",
                    role="核心视角人物",
                    personality="谨慎、执着、在压力下会主动承担责任",
                    current_goal="理解初始异常并保护最重要的人",
                    key_memories="第一次接触异常时失去了稳定生活",
                    relationships="与关键同伴从互相怀疑走向合作",
                    writing_notes="成长要循序渐进，避免一开始就无所不能",
                ),
                CharacterDraft(
                    name="关键同伴",
                    role="掌握部分真相的同行者",
                    personality="敏锐、克制、习惯隐藏自己的真实目的",
                    current_goal="确认主角是否值得信任",
                    key_memories="曾因同一异常付出代价",
                    relationships="既帮助主角，也保留关键秘密",
                    writing_notes="台词应有信息差，不要提前解释全部谜底",
                ),
            ],
            chapters=[
                ChapterPlanDraft(number=1, title="异常出现"),
                ChapterPlanDraft(number=2, title="规则代价"),
                ChapterPlanDraft(number=3, title="第一次选择"),
            ],
        )

    def generate_chapter(self, prompt_package: str) -> ChapterGenerationResult:
        content = (
            "第一章\n\n"
            f"根据提示包：{prompt_package[:120]}，主角在日常秩序被打破的时刻第一次面对异常。"
            "他没有立刻理解真相，只能先保存线索、确认身边人的安全，并做出一个会影响后续章节的选择。"
        )
        return ChapterGenerationResult(
            content=content,
            summary="主角遭遇初始异常，确认事件并非偶然，后续需要追查规则来源。",
            character_updates=["主角开始从旁观者转向行动者。"],
            foreshadowing_updates=["异常出现时留下一个尚未解释的细节。"],
        )

    def review_chapter(self, content: str, prompt_package: str) -> list[ReviewFindingDraft]:
        return [
            ReviewFindingDraft(
                problem_type="basic_consistency",
                message="草稿围绕本章目标推进，未发现阻塞性冲突。",
                suggestion="采纳前可补充一个更具体的结尾钩子。",
                blocking=False,
            )
        ]

    def summarize_chapter(self, content: str) -> str:
        first_line = content.strip().splitlines()[0] if content.strip() else "空章节"
        return f"{first_line}：本章完成关键事件推进，并留下后续生成可引用的摘要。"

    def judge_foreshadowing(self, content: str, context: str, existing_items: list[str]) -> dict[str, Any]:
        return {
            "new": ["异常出现时留下一个尚未解释的细节。"],
            "advanced": existing_items[:1] or ["初始异常细节被推进。"],
            "resolved": [],
            "leaked": [],
            "notes": "伏笔未提前泄露，适合继续保留。",
        }

    def judge_character_period(self, content: str, context: str, characters: list[str]) -> dict[str, Any]:
        return {
            "updates": ["主角开始从旁观者转向行动者。"],
            "new_period_cards": [],
            "relationship_changes": [],
            "memory_changes": ["主角确认异常会影响稳定生活。"],
            "stage_changed": False,
        }

    def propose_future_plan_updates(self, content: str, context: str, chapters: list[str]) -> dict[str, Any]:
        return {
            "suggestions": [
                {
                    "chapter": chapters[1] if len(chapters) > 1 else "第 2 章",
                    "change": "强化第一次付出代价的目标。",
                }
            ],
            "notes": "本章已经完成初始异常确认，后续应承接代价验证。",
        }

    def review_user_input(self, input_kind: str, content: str, context: str) -> UserInputReviewResult:
        text = content.strip()
        if len(text) < 8:
            return UserInputReviewResult(
                decision="block",
                reason="输入过于模糊，无法稳定指导后续生成。",
                suggestions=["补充主角、核心异常、冲突目标或故事约束。"],
            )
        if any(marker in text for marker in ("提前泄露", "所有伏笔", "直接解释真相")):
            return UserInputReviewResult(
                decision="block",
                reason="输入可能提前泄露伏笔或一次性解释关键真相。",
                suggestions=["改成只推进一个线索，保留真相揭示节奏。"],
            )
        if len(text) < 20:
            return UserInputReviewResult(
                decision="warning",
                reason="输入可用，但信息较少，后续生成可控性有限。",
                suggestions=["增加具体场景、人物选择或限制条件。"],
            )
        return UserInputReviewResult(
            decision="pass",
            reason="输入与当前创作方向兼容，可以进入后续上下文。",
            suggestions=[],
        )
