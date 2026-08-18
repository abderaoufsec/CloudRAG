import json
from pathlib import Path

import faiss
import numpy as np

from app.rag.chunker import TextChunk


class VectorStore:
    def __init__(self, index_directory: Path):
        self.index_directory = Path(index_directory)

        self.index_path = (
            self.index_directory / "cloudrag.index"
        )

        self.metadata_path = (
            self.index_directory / "metadata.json"
        )

        self.index_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index = None
        self.metadata = []

        self._load()

    def _load(self):
        if self.index_path.exists():
            self.index = faiss.read_index(
                str(self.index_path)
            )

        if self.metadata_path.exists():
            self.metadata = json.loads(
                self.metadata_path.read_text(
                    encoding="utf-8"
                )
            )

    def _save(self):
        if self.index is not None:
            faiss.write_index(
                self.index,
                str(self.index_path),
            )

        self.metadata_path.write_text(
            json.dumps(
                self.metadata,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def add_chunks(
        self,
        chunks: list[TextChunk],
        embeddings,
    ):
        if not chunks:
            return

        vectors = np.asarray(
            embeddings,
            dtype="float32",
        )

        dimension = vectors.shape[1]

        if self.index is None:
            self.index = faiss.IndexFlatIP(
                dimension
            )

        self.index.add(vectors)

        for chunk in chunks:
            self.metadata.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                }
            )

        self._save()

    def search(
        self,
        query_embedding,
        top_k: int = 5,
    ):
        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        query_vector = np.asarray(
            query_embedding,
            dtype="float32",
        )

        scores, indices = self.index.search(
            query_vector,
            min(top_k, self.index.ntotal),
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            metadata = self.metadata[index]

            results.append(
                {
                    **metadata,
                    "score": float(score),
                }
            )

        return results

    @property
    def size(self) -> int:
        if self.index is None:
            return 0

        return self.index.ntotal