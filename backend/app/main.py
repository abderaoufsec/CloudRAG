from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.rag import router as rag_router
from app.config import get_settings
from app.db.init_db import initialize_database


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_database()

    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Multilingual document-grounded AI assistant "
        "using Retrieval-Augmented Generation."
    ),
    lifespan=lifespan,
)


app.include_router(health_router)
app.include_router(documents_router)
app.include_router(rag_router)


@app.get("/")
def root():

    return {
        "message": "CloudRAG API is running",
        "docs": "/docs",
        "health": "/api/health",
        "documents": "/api/documents",
        "rag": "/api/rag",
    }