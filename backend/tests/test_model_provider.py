from app.services.model_provider import DeepSeekAnthropicProvider, MockModelProvider


def test_mock_provider_returns_structured_project_setup():
    provider = MockModelProvider()

    result = provider.generate_project_setup("一个月球茶馆老板调查失踪诗人的故事")

    assert result.positioning
    assert len(result.characters) >= 2
    assert len(result.chapters) >= 3


def test_deepseek_provider_parses_project_setup_json():
    transport = FakeTransport(
        {
            "title": "废城修书人",
            "positioning": "悬念长篇",
            "worldview": "书会改写现实",
            "main_plot": "主角追查书的规则",
            "characters": [
                {
                    "name": "修书人",
                    "role": "主角",
                    "personality": "克制",
                    "current_goal": "找回记忆",
                    "key_memories": "醒在废城",
                    "relationships": "与向导互相试探",
                    "writing_notes": "保持疑问",
                }
            ],
            "chapters": [{"number": 1, "title": "异常出现"}],
        }
    )
    provider = DeepSeekAnthropicProvider(
        api_key="test-key",
        base_url="https://api.example.com/anthropic",
        model="deepseek-v4-flash",
        transport=transport,
    )

    result = provider.generate_project_setup("一个失忆修书人的故事")

    assert result.title == "废城修书人"
    assert result.characters[0].name == "修书人"
    assert result.chapters[0].title == "异常出现"
    assert transport.requests[0]["url"] == "https://api.example.com/anthropic/v1/messages"
    assert transport.requests[0]["payload"]["model"] == "deepseek-v4-flash"


def test_deepseek_provider_parses_chapter_generation_json():
    transport = FakeTransport(
        {
            "content": "第一章\n\n修书人醒来。",
            "summary": "主角醒在废城。",
            "character_updates": ["主角开始行动"],
            "foreshadowing_updates": ["书页发光"],
        }
    )
    provider = DeepSeekAnthropicProvider(
        api_key="test-key",
        base_url="https://api.example.com/anthropic/",
        model="deepseek-v4-flash",
        transport=transport,
    )

    result = provider.generate_chapter("章节提示包")

    assert "修书人醒来" in result.content
    assert result.summary == "主角醒在废城。"
    assert result.character_updates == ["主角开始行动"]
    assert result.foreshadowing_updates == ["书页发光"]


def test_mock_provider_returns_llm_judge_eval_result():
    provider = MockModelProvider()

    result = provider.judge_eval_case(
        input_text="主角保持目标继续追查。",
        context="主角目标是找回记忆。",
        rubric="检查人设一致性和伏笔泄露。",
    )

    assert result.scores["consistency"] > 0
    assert result.reason
    assert result.blocking_findings == []


def test_deepseek_provider_parses_llm_judge_eval_json():
    transport = FakeTransport(
        {
            "scores": {
                "consistency": 0.9,
                "character": 0.8,
                "foreshadowing": 1.0,
                "style": 0.7,
            },
            "blocking_findings": ["伏笔提前泄露"],
            "reason": "整体可用，但结尾直接解释了伏笔。",
        }
    )
    provider = DeepSeekAnthropicProvider(
        api_key="test-key",
        base_url="https://api.example.com/anthropic",
        model="deepseek-v4-flash",
        transport=transport,
    )

    result = provider.judge_eval_case(
        input_text="章节正文",
        context="项目上下文",
        rubric="按 0-1 分评估。",
    )

    assert result.scores["consistency"] == 0.9
    assert result.scores["foreshadowing"] == 1.0
    assert result.blocking_findings == ["伏笔提前泄露"]
    assert "直接解释" in result.reason
    assert "scores" in transport.requests[0]["payload"]["messages"][0]["content"]


class FakeTransport:
    def __init__(self, payload: dict):
        self.payload = payload
        self.requests: list[dict] = []

    def __call__(self, url: str, headers: dict[str, str], payload: dict) -> dict:
        self.requests.append({"url": url, "headers": headers, "payload": payload})
        return {"content": [{"type": "text", "text": self._text()}]}

    def _text(self) -> str:
        import json

        return json.dumps(self.payload, ensure_ascii=False)
