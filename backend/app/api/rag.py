from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import structlog

from app.db.database import get_db
from app.rag.pipeline import rag_pipeline
from app.providers.base import LLMProviderError
from app.services.document_repository import (
    get_document,
)

logger = structlog.get_logger()


router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
)


class IndexRequest(BaseModel):
    document_id: str

    text: str = Field(
        min_length=1,
        description="Extracted document text.",
    )


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        description="Question or search query.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        description=(
            "Question about indexed documents."
        ),
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    document_id: str | None = Field(
        default=None,
        description="Optionally restrict retrieval to one indexed document.",
    )


@router.post("/index")
def index_document(
    request: IndexRequest,
):
    result = rag_pipeline.index_document(
        document_id=request.document_id,
        text=request.text,
    )

    return {
        "success": True,
        "message": (
            "Document indexed successfully."
        ),
        "result": result,
    }


@router.post("/search")
def search(
    request: SearchRequest,
):

    results = rag_pipeline.search(
        query=request.query,
        top_k=request.top_k,
    )

    return {
        "success": True,
        "query": request.query,
        "results": results,
    }


@router.post("/ask")
def ask(
    request: AskRequest,
    db: Session = Depends(get_db),
):

    if request.document_id and not get_document(db, request.document_id):
        logger.warning(
            "rag_ask_document_not_found",
            document_id=request.document_id,
            question=request.question,
        )
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        result = rag_pipeline.ask(
            question=request.question,
            top_k=request.top_k,
            document_id=request.document_id,
        )
    except LLMProviderError as exc:
        logger.error(
            "rag_ask_llm_provider_error",
            question=request.question,
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The local AI service is unavailable. Check Ollama and the configured model.",
        ) from exc

    enriched_sources = []

    for source in result["sources"]:

        document = get_document(
            db,
            source["document_id"],
        )

        enriched_sources.append(
            {
                **source,
                "filename": (
                    document.filename
                    if document
                    else source["document_id"]
                ),
            }
        )

    logger.info(
        "rag_ask_completed",
        question=request.question,
        top_k=request.top_k,
        sources_count=len(enriched_sources),
        document_id=request.document_id,
    )

    return {
        "success": True,
        "question": request.question,
        "answer": result["answer"],
        "sources": enriched_sources,
    }


@router.get("/stats")
def stats():

    return {
        "vector_count":
            rag_pipeline.vector_store.size,
    }
