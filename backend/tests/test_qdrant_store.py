from pathlib import Path

import numpy as np
import pytest

from app.rag.chunker import TextChunk
from app.rag.vector_store import QdrantVectorStore, VectorStoreError


class FakePoint:
    def __init__(self, payload, score):
        self.payload = payload
        self.score = score


class FakeResponse:
    def __init__(self, points):
        self.points = points


def _make_store(client):
    store = object.__new__(QdrantVectorStore)
    store.client = client
    store.collection_name = "test"
    store.metadata = []
    store.index_directory = Path(".")
    return store


def _chunk():
    return TextChunk(
        chunk_id="doc_0",
        document_id="doc",
        text="hello world",
        chunk_index=0,
        page=1,
    )


def test_search_error_raises_vector_store_error():
    class ErrorClient:
        def query_points(self, **_kwargs):
            raise RuntimeError("connection lost")

        def search(self, **_kwargs):
            raise RuntimeError("connection lost")

    store = _make_store(ErrorClient())

    with pytest.raises(VectorStoreError):
        store.search([0.1, 0.2, 0.3], top_k=2)


def test_add_chunks_deletes_existing_document_before_upsert():
    class RecordingClient:
        def __init__(self):
            self.calls = []

        def get_collection(self, **_kwargs):
            return object()

        def delete(self, **kwargs):
            self.calls.append(("delete", kwargs))

        def upsert(self, **kwargs):
            self.calls.append(("upsert", kwargs))

    client = RecordingClient()
    store = _make_store(client)

    store.add_chunks(
        [_chunk()],
        np.array([[0.1, 0.2, 0.3]], dtype="float32"),
    )

    names = [name for name, _ in client.calls]

    assert "delete" in names
    assert "upsert" in names
    assert names.index("delete") < names.index("upsert")

    delete_kwargs = client.calls[names.index("delete")][1]
    points_selector = delete_kwargs["points_selector"]

    assert points_selector.must[0].key == "document_id"
    assert points_selector.must[0].match.value == "doc"


def test_search_maps_payload_fields():
    class OkClient:
        def query_points(self, **kwargs):
            assert kwargs["query"] == pytest.approx(
                [0.1, 0.2, 0.3]
            )
            return FakeResponse(
                [
                    FakePoint(
                        {
                            "chunk_id": "doc_0",
                            "document_id": "doc",
                            "chunk_index": 0,
                            "text": "hello world",
                            "page": 1,
                        },
                        0.88,
                    )
                ]
            )

    store = _make_store(OkClient())

    results = store.search([0.1, 0.2, 0.3], top_k=1)

    assert results == [
        {
            "chunk_id": "doc_0",
            "document_id": "doc",
            "chunk_index": 0,
            "text": "hello world",
            "score": 0.88,
            "page": 1,
        }
    ]
