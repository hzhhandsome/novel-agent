from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://novel:novel@localhost:5432/novel_agent"
    model_provider: str = "mock"
    model_base_url: str = "https://api.deepseek.com/anthropic"
    model_api_key: str = ""
    model_name: str = "deepseek-v4-flash"
    model_max_tokens: int = 4096

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_prefix="NOVEL_AGENT_",
        protected_namespaces=("settings_",),
    )


settings = Settings()
