import structlog
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.rag.pipeline import rag_pipeline


logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health_check():
    """
    Health endpoint confirms the application process is alive.
    This is a lightweight check that doesn't verify external dependencies.
    """
    settings = get_settings()

    return {
        "status": "ok",
        "project": settings.app_name,
        "version": settings.app_version,
        "mode": settings.llm_provider,
    }


@router.get("/ready")
def readiness_check():
    """
    Readiness endpoint verifies critical dependencies are available.
    Checks database, vector store, embedding provider, and LLM provider.
    Returns 503 if any critical dependency is unavailable.
    """
    checks = {
        "database": "unknown",
        "vector_store": "unknown",
        "embedding_provider": "unknown",
        "llm_provider": "unknown",
    }

    try:
        # Check database connection
        from app.db.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ready"
    except Exception:
        logger.exception("readiness_database_failed")
        checks["database"] = "unavailable"

    try:
        # Check vector store
        vector_size = rag_pipeline.vector_store.size
        checks["vector_store"] = f"ready ({vector_size} vectors)"
    except Exception:
        logger.exception("readiness_vector_store_failed")
        checks["vector_store"] = "unavailable"

    try:
        # Report embedding readiness without loading the model here.
        from app.rag.embeddings import get_embedding_model
        if get_embedding_model.cache_info().currsize > 0:
            checks["embedding_provider"] = "ready"
        else:
            checks["embedding_provider"] = "not_loaded"
    except Exception:
        logger.exception("readiness_embedding_provider_failed")
        checks["embedding_provider"] = "unavailable"

    try:
        # Check the local LLM provider cheaply and truthfully.
        settings = get_settings()
        if settings.llm_provider == "local":
            from ollama import Client
            Client(
                host=settings.ollama_base_url,
                timeout=2,
            ).list()
            checks["llm_provider"] = "ready (local)"
        else:
            checks["llm_provider"] = f"configured ({settings.llm_provider})"
    except Exception:
        logger.exception("readiness_llm_provider_failed")
        checks["llm_provider"] = "unavailable"

    # Determine overall readiness
    all_ready = all(
        check.startswith("ready")
        or check.startswith("configured")
        or check == "not_loaded"
        for check in checks.values()
    )

    if not all_ready:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "checks": checks,
            }
        )

    return {
        "status": "ready",
        "checks": checks,
    }
