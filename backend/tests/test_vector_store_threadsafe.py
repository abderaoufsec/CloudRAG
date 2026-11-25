import threading

import numpy as np

from app.rag.chunker import TextChunk
from app.rag.vector_store import VectorStore


DIMENSION = 8
CHUNKS_PER_DOCUMENT = 3
DOCUMENT_COUNT = 8


def _chunks(document_index: int):
    return [
        TextChunk(
            chunk_id=f"doc-{document_index}_{chunk_index}",
            document_id=f"doc-{document_index}",
            text=f"text {document_index} {chunk_index}",
            chunk_index=chunk_index,
        )
        for chunk_index in range(CHUNKS_PER_DOCUMENT)
    ]


def test_concurrent_adds_keep_index_and_metadata_consistent(tmp_path):
    store = VectorStore(tmp_path)

    def worker(document_index):
        embeddings = np.random.RandomState(
            document_index
        ).rand(
            CHUNKS_PER_DOCUMENT,
            DIMENSION,
        ).astype("float32")
        store.add_chunks(
            _chunks(document_index),
            embeddings,
        )

    threads = [
        threading.Thread(
            target=worker,
            args=(document_index,),
        )
        for document_index in range(DOCUMENT_COUNT)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert store.size == DOCUMENT_COUNT * CHUNKS_PER_DOCUMENT
    assert len(store.metadata) == store.index.ntotal


def test_save_writes_through_temporary_files(
    tmp_path,
    monkeypatch,
):
    import app.rag.vector_store as vector_store_module

    replacements = []
    real_replace = vector_store_module.os.replace

    def tracking_replace(source, destination):
        replacements.append(
            (str(source), str(destination))
        )
        return real_replace(source, destination)

    monkeypatch.setattr(
        vector_store_module.os,
        "replace",
        tracking_replace,
    )

    store = VectorStore(tmp_path)

    store.add_chunks(
        _chunks(0),
        np.random.RandomState(0).rand(
            CHUNKS_PER_DOCUMENT,
            DIMENSION,
        ).astype("float32"),
    )

    destinations = {destination for _, destination in replacements}

    assert str(store.index_path) in destinations
    assert str(store.metadata_path) in destinations
    assert not (tmp_path / "cloudrag.index.tmp").exists()
    assert not (tmp_path / "metadata.json.tmp").exists()
