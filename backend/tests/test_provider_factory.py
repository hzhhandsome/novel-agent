from types import SimpleNamespace

import pytest

from app.services.model_provider import DeepSeekAnthropicProvider, MockModelProvider
from app.services.provider_factory import get_model_provider


def test_factory_returns_mock_provider_by_default():
    settings = SimpleNamespace(model_provider="mock")

    provider = get_model_provider(settings)

    assert isinstance(provider, MockModelProvider)


def test_factory_returns_deepseek_provider_from_settings():
    settings = SimpleNamespace(
        model_provider="deepseek",
        model_api_key="test-key",
        model_base_url="https://api.deepseek.com/anthropic",
        model_name="deepseek-v4-flash",
        model_max_tokens=2048,
    )

    provider = get_model_provider(settings)

    assert isinstance(provider, DeepSeekAnthropicProvider)
    assert provider.model == "deepseek-v4-flash"
    assert provider.base_url == "https://api.deepseek.com/anthropic"


def test_factory_rejects_unknown_provider():
    settings = SimpleNamespace(model_provider="unknown")

    with pytest.raises(ValueError, match="Unsupported model provider"):
        get_model_provider(settings)
