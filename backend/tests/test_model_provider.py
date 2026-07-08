from app.services.model_provider import MockModelProvider


def test_mock_provider_returns_structured_project_setup():
    provider = MockModelProvider()

    result = provider.generate_project_setup("一个月球茶馆老板调查失踪诗人的故事")

    assert result.positioning
    assert len(result.characters) >= 2
    assert len(result.chapters) >= 3
