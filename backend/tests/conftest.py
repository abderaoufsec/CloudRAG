from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


class StubRAGPipeline:
    def index_document(self, document_id: str, text: str) -> dict:
        return {
            "document_id": document_id,
            "chunks": 1,
            "vector_store_size": 1,
        }

    def delete_document(self, document_id: str) -> None:
        return None


@pytest.fixture
def documents_client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    """Provide an isolated database, filesystem, and RAG pipeline."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    import app.api.documents as documents_api

    monkeypatch.setattr(documents_api, "DOCUMENTS_DIR", tmp_path / "documents")
    monkeypatch.setattr(documents_api, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(documents_api, "rag_pipeline", StubRAGPipeline())
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    engine.dispose()
