from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multilingual document-grounded AI assistant using RAG.",
)

app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "CloudRAG API is running",
        "docs": "/docs",
        "health": "/api/health",
    }