from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import structlog

from app.db.database import get_db
from app.rag.pipeline import rag_pipeline
from app.rag.vector_store import VectorStoreError
from app.providers.base import LLMProviderError
from app.services.document_repository import (
    get_document,
    get_documents_by_ids,
)

logger = structlog.get_logger()


router = APIRouter(
    prefix="/api/rag",
    tags=["rag"],
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

    document_id: str | None = Field(
        default=None,
        description="Optionally restrict search to one indexed document.",
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


@router.post("/search")
def search(
    request: SearchRequest,
    db: Session = Depends(get_db),
):

    if request.document_id and not get_document(db, request.document_id):
        logger.warning(
            "rag_search_document_not_found",
            document_id=request.document_id,
            query_length=len(request.query),
        )
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        results = rag_pipeline.search(
            query=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )
    except VectorStoreError as exc:
        logger.error(
            "rag_search_vector_store_error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector store is unavailable.",
        ) from exc

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
            question_length=len(request.question),
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
            question_length=len(request.question),
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The local AI service is unavailable. Check Ollama and the configured model.",
        ) from exc
    except VectorStoreError as exc:
        logger.error(
            "rag_ask_vector_store_error",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The vector store is unavailable.",
        ) from exc

    document_ids = {
        source["document_id"]
        for source in result["sources"]
    }

    documents_by_id = get_documents_by_ids(
        db,
        list(document_ids),
    )

    enriched_sources = [
        {
            **source,
            "filename": (
                documents_by_id[
                    source["document_id"]
                ].filename
                if source["document_id"] in documents_by_id
                else source["document_id"]
            ),
        }
        for source in result["sources"]
    ]

    logger.info(
        "rag_ask_completed",
        question_length=len(request.question),
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
