from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://novel:novel@localhost:5432/novel_agent"
    model_provider: str = "mock"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_prefix="NOVEL_AGENT_",
        protected_namespaces=("settings_",),
    )


settings = Settings()
