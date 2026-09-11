import numpy as np

from app.rag.chunker import TextChunk
from app.rag.vector_store import VectorStore


def test_search_can_be_restricted_to_one_document(tmp_path):
    store = VectorStore(tmp_path)
    chunks = [
        TextChunk(
            chunk_id="a-0", document_id="document-a", text="A", chunk_index=0
        ),
        TextChunk(
            chunk_id="b-0", document_id="document-b", text="B", chunk_index=0
        ),
    ]
    store.add_chunks(
        chunks,
        np.array([[1.0, 0.0], [0.99, 0.01]], dtype="float32"),
    )

    results = store.search(
        np.array([[1.0, 0.0]], dtype="float32"),
        top_k=1,
        document_id="document-b",
    )

    assert [result["document_id"] for result in results] == ["document-b"]
