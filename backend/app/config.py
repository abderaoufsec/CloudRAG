from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "CloudRAG"
    app_version: str = "0.1.0"
    environment: str = "development"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    trusted_hosts: str = "localhost,127.0.0.1,testserver"

    llm_provider: str = "local"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"
    ollama_timeout_seconds: float = 120.0
    embedding_provider: str = "local"
    vector_store: str = "faiss"

    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "cloudrag"

    max_upload_size_mb: int = 10
    # The multilingual MiniLM embedding model produces lower absolute cosine
    # scores for some Arabic and cross-language queries than for English.
    # 0.30 still rejects weak matches while allowing verified multilingual
    # evidence through to the grounded-answer step.
    min_retrieval_score: float = 0.30
    max_rag_context_characters: int = 12000

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def trusted_host_list(self) -> list[str]:
        return [
            host.strip()
            for host in self.trusted_hosts.split(",")
            if host.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
