from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.rag.pipeline import rag_pipeline


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
        "environment": settings.environment,
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
    except Exception as exc:
        checks["database"] = f"unavailable: {str(exc)}"

    try:
        # Check vector store
        vector_size = rag_pipeline.vector_store.size
        checks["vector_store"] = f"ready ({vector_size} vectors)"
    except Exception as exc:
        checks["vector_store"] = f"unavailable: {str(exc)}"

    try:
        # Check embedding provider
        from app.rag.embeddings import get_embedding_model
        model = get_embedding_model()
        checks["embedding_provider"] = f"ready ({model})"
    except Exception as exc:
        checks["embedding_provider"] = f"unavailable: {str(exc)}"

    try:
        # Check LLM provider
        settings = get_settings()
        if settings.llm_provider == "local":
            from app.providers.factory import get_llm_provider
            provider = get_llm_provider()
            checks["llm_provider"] = f"ready ({settings.llm_provider})"
        else:
            checks["llm_provider"] = f"configured ({settings.llm_provider})"
    except Exception as exc:
        checks["llm_provider"] = f"unavailable: {str(exc)}"

    # Determine overall readiness
    all_ready = all(
        check.startswith("ready") or check.startswith("configured")
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