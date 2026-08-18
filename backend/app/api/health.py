from fastapi import APIRouter

from app.config import get_settings


router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health")
def health_check():
    settings = get_settings()

    return {
        "status": "ok",
        "project": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "mode": settings.llm_provider,
    }