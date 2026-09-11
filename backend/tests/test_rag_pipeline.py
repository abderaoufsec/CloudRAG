from unittest.mock import Mock

from app.rag.chunker import create_chunks
from app.rag.pipeline import RAGPipeline


def test_rag_chunk_creation():

    text = """
    Retrieval-Augmented Generation combines
    information retrieval with language models.

    The retrieval system finds relevant information
    from a knowledge base before generating an answer.
    """

    chunks = create_chunks(
        text=text,
        document_id="rag-test",
        chunk_size=100,
        chunk_overlap=20,
    )

    assert len(chunks) >= 2

    assert all(
        chunk.document_id == "rag-test"
        for chunk in chunks
    )

    assert all(
        chunk.text
        for chunk in chunks
    )


def test_rag_search_uses_cache(monkeypatch):
    pipeline = object.__new__(RAGPipeline)
    pipeline.vector_store = Mock()
    pipeline.vector_store.search.return_value = [
        {"document_id": "doc", "chunk_id": "doc_0", "chunk_index": 0, "score": 0.9, "text": "cached retrieval"}
    ]
    monkeypatch.setattr("app.rag.pipeline.embed_query", lambda query: [0.1, 0.2])

    first = pipeline.search("What is AI?", top_k=3)
    second = pipeline.search("What is AI?", top_k=3)

    assert len(first) == 1
    assert first == second
    assert pipeline.vector_store.search.call_count == 1
