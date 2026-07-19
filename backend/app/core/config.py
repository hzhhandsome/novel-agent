from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://novel:novel@localhost:5432/novel_agent"
    model_provider: str = "mock"
    model_base_url: str = "https://api.deepseek.com/anthropic"
    model_api_key: str = ""
    model_name: str = "deepseek-v4-flash"
    model_max_tokens: int = 4096
    retrieval_backend: str = "local"
    retrieval_top_k: int = 8
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "novel_agent_memory"
    embedding_provider: str = "hash"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimension: int = 384
    model_input_cost_per_1k: float = 0.0
    model_output_cost_per_1k: float = 0.0

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_prefix="NOVEL_AGENT_",
        protected_namespaces=("settings_",),
    )


settings = Settings()
