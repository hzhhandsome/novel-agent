from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


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


class ModelProvider(Protocol):
    def generate_project_setup(self, idea: str) -> ProjectSetupResult:
        raise NotImplementedError

    def generate_chapter(self, prompt_package: str) -> ChapterGenerationResult:
        raise NotImplementedError

    def review_chapter(self, content: str, prompt_package: str) -> list[ReviewFindingDraft]:
        raise NotImplementedError

    def summarize_chapter(self, content: str) -> str:
        raise NotImplementedError


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
