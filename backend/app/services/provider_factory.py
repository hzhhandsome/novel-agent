from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings
from app.services.model_provider import DeepSeekAnthropicProvider, MockModelProvider, ModelProvider


@dataclass
class RuntimeModelConfig:
    provider: str
    base_url: str
    model: str
    max_tokens: int
    api_key: str = ""


_runtime_model_config = RuntimeModelConfig(
    provider=settings.model_provider,
    base_url=settings.model_base_url,
    model=settings.model_name,
    max_tokens=settings.model_max_tokens,
    api_key=settings.model_api_key,
)


def get_model_provider(settings_override=None) -> ModelProvider:
    config = _config_from_settings(settings_override) if settings_override else _runtime_model_config
    return _provider_from_config(config)


def get_model_provider_from_snapshot(snapshot: dict | None = None) -> ModelProvider:
    if not snapshot:
        return get_model_provider()
    config = RuntimeModelConfig(
        provider=str(snapshot.get("provider") or _runtime_model_config.provider),
        base_url=str(snapshot.get("base_url") or _runtime_model_config.base_url),
        model=str(snapshot.get("model") or _runtime_model_config.model),
        max_tokens=int(snapshot.get("max_tokens") or _runtime_model_config.max_tokens),
        api_key=_runtime_model_config.api_key,
    )
    return _provider_from_config(config)


def get_current_model_config() -> dict:
    return _public_config(_runtime_model_config)


def get_model_config_snapshot() -> dict:
    return _public_config(_runtime_model_config)


def update_runtime_model_config(
    provider: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
) -> dict:
    if provider is not None:
        _runtime_model_config.provider = provider
    if base_url is not None:
        _runtime_model_config.base_url = base_url
    if model is not None:
        _runtime_model_config.model = model
    if max_tokens is not None:
        _runtime_model_config.max_tokens = max_tokens
    if api_key is not None:
        _runtime_model_config.api_key = api_key
    return get_current_model_config()


def _provider_from_config(config: RuntimeModelConfig) -> ModelProvider:
    provider_name = config.provider.lower()

    if provider_name == "mock":
        return MockModelProvider()
    if provider_name == "deepseek":
        return DeepSeekAnthropicProvider(
            api_key=config.api_key,
            base_url=config.base_url,
            model=config.model,
            max_tokens=config.max_tokens,
        )

    raise ValueError(f"Unsupported model provider: {config.provider}")


def _config_from_settings(active_settings) -> RuntimeModelConfig:
    return RuntimeModelConfig(
        provider=active_settings.model_provider,
        base_url=getattr(active_settings, "model_base_url", settings.model_base_url),
        model=getattr(active_settings, "model_name", settings.model_name),
        max_tokens=getattr(active_settings, "model_max_tokens", settings.model_max_tokens),
        api_key=getattr(active_settings, "model_api_key", ""),
    )


def _public_config(config: RuntimeModelConfig) -> dict:
    return {
        "provider": config.provider,
        "base_url": config.base_url,
        "model": config.model,
        "max_tokens": config.max_tokens,
        "api_key_set": bool(config.api_key),
    }
