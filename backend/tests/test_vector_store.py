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


def test_idempotent_indexing_prevents_duplicates(tmp_path):
    """
    Test that re-indexing the same document doesn't create duplicate vectors.
    Idempotent indexing is critical for reliable document updates.
    """
    store = VectorStore(tmp_path)

    # First indexing
    chunks = [
        TextChunk(
            chunk_id="doc1-0", document_id="document-1", text="First chunk", chunk_index=0
        ),
        TextChunk(
            chunk_id="doc1-1", document_id="document-1", text="Second chunk", chunk_index=1
        ),
    ]
    store.add_chunks(
        chunks,
        np.array([[1.0, 0.0], [0.5, 0.5]], dtype="float32"),
    )

    first_size = store.size
    assert first_size == 2

    # Re-index the same document (simulating a document update)
    # In a real scenario, chunk_ids would be regenerated, but document_id stays the same
    updated_chunks = [
        TextChunk(
            chunk_id="doc1-updated-0", document_id="document-1", text="Updated first chunk", chunk_index=0
        ),
        TextChunk(
            chunk_id="doc1-updated-1", document_id="document-1", text="Updated second chunk", chunk_index=1
        ),
    ]
    store.add_chunks(
        updated_chunks,
        np.array([[0.9, 0.1], [0.4, 0.6]], dtype="float32"),
    )

    # Size should still be 2, not 4 (no duplicates)
    second_size = store.size
    assert second_size == 2, f"Expected 2 vectors after re-indexing, got {second_size}"

    # Metadata should only have 2 entries
    assert len(store.metadata) == 2, f"Expected 2 metadata entries, got {len(store.metadata)}"

    # All metadata should belong to the same document
    doc_ids = {m["document_id"] for m in store.metadata}
    assert doc_ids == {"document-1"}, f"Expected only document-1, got {doc_ids}"
