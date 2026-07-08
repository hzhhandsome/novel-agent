from __future__ import annotations

from app.core.config import settings
from app.services.model_provider import DeepSeekAnthropicProvider, MockModelProvider, ModelProvider


def get_model_provider(settings_override=None) -> ModelProvider:
    active_settings = settings_override or settings
    provider_name = active_settings.model_provider.lower()

    if provider_name == "mock":
        return MockModelProvider()
    if provider_name == "deepseek":
        return DeepSeekAnthropicProvider(
            api_key=active_settings.model_api_key,
            base_url=active_settings.model_base_url,
            model=active_settings.model_name,
            max_tokens=active_settings.model_max_tokens,
        )

    raise ValueError(f"Unsupported model provider: {active_settings.model_provider}")
