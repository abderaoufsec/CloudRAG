from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CloudRAG"
    app_version: str = "0.1.0"
    environment: str = "development"

    llm_provider: str = "local"
    embedding_provider: str = "local"
    vector_store: str = "faiss"

    max_upload_size_mb: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()