from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.rag.pipeline import rag_pipeline


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
        description="Question about the indexed documents.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )


@router.post("/index")
def index_document(request: IndexRequest):

    result = rag_pipeline.index_document(
        document_id=request.document_id,
        text=request.text,
    )

    return {
        "success": True,
        "message": "Document indexed successfully.",
        "result": result,
    }


@router.post("/search")
def search(request: SearchRequest):

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
def ask(request: AskRequest):

    result = rag_pipeline.ask(
        question=request.question,
        top_k=request.top_k,
    )

    return {
        "success": True,
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
    }


@router.get("/stats")
def stats():

    return {
        "vector_count": rag_pipeline.vector_store.size,
    }