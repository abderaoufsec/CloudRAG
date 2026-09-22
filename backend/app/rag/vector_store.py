import json
import uuid
from pathlib import Path

import faiss
import numpy as np

from app.config import get_settings
from app.rag.chunker import TextChunk

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointStruct,
        VectorParams,
    )
except Exception:  # pragma: no cover - optional dependency
    QdrantClient = None
    Distance = None
    FieldCondition = None
    Filter = None
    MatchValue = None
    PointStruct = None
    VectorParams = None


class QdrantVectorStore:
    """
    Optional remote vector store adapter for a Qdrant Cloud cluster.
    Keeps the same public search/add/delete API used by the RAG pipeline.
    """

    def __init__(self, index_directory: Path | None = None):
        self.settings = get_settings()
        if QdrantClient is None or Filter is None or PointStruct is None:
            raise RuntimeError(
                "qdrant-client is not installed. Install backend requirements before using Qdrant Cloud."
            )
        if not self.settings.qdrant_url:
            raise RuntimeError("QDRANT_URL must be set before selecting qdrant vector_store.")
        if not self.settings.qdrant_api_key:
            raise RuntimeError("QDRANT_API_KEY must be set before selecting qdrant vector_store.")

        self.collection_name = self.settings.qdrant_collection
        self.client = QdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
            prefer_grpc=False,
            check_compatibility=False,
        )
        self.index_directory = Path(index_directory) if index_directory else Path(".")
        self.metadata = []

    def _ensure_collection(self, dimension: int):
        try:
            self.client.get_collection(collection_name=self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def add_chunks(self, chunks: list[TextChunk], embeddings):
        """
        Add chunks to Qdrant. Uses deterministic UUIDs based on chunk_id,
        making the operation idempotent - re-indexing the same document
        will update existing vectors rather than create duplicates.
        """
        if not chunks:
            return

        vectors = np.asarray(embeddings, dtype="float32")
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        dimension = int(vectors.shape[1])
        self._ensure_collection(dimension)

        points = []
        for chunk, vector in zip(chunks, vectors):
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "page": chunk.page,  # Include page number for citations
            }
            # Qdrant Cloud requires point IDs to be a UUID or an unsigned int.
            # The existing chunk_id format is document_id_chunk_index.
            # Convert that semantic key into a deterministic UUID.
            # This makes upsert idempotent - same chunk_id = same UUID = updates existing point.
            deterministic_id = str(
                uuid.uuid5(
                    namespace=uuid.NAMESPACE_DNS,
                    name=f"cloudrag:{chunk.chunk_id}",
                )
            )
            points.append(
                PointStruct(
                    id=deterministic_id,
                    vector=vector.tolist(),
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points,
        )

    def delete_document(self, document_id: str):
        qfilter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qfilter,
            wait=True,
        )

    def search(self, query_embedding, top_k: int = 5, document_id: str | None = None):
        if query_embedding is None:
            return []

        query_vector = np.asarray(query_embedding, dtype="float32").reshape(-1).tolist()
        qfilter = None
        if document_id:
            qfilter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )

        try:
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qfilter,
                limit=top_k,
                with_payload=True,
            )
        except Exception:
            return []

        results = []
        for hit in hits:
            payload = hit.payload or {}
            results.append(
                {
                    "chunk_id": payload.get("chunk_id"),
                    "document_id": payload.get("document_id"),
                    "chunk_index": payload.get("chunk_index"),
                    "text": payload.get("text"),
                    "score": float(hit.score),
                    "page": payload.get("page"),  # Include page number
                }
            )
        return results

    @property
    def size(self) -> int:
        try:
            collection = self.client.get_collection(collection_name=self.collection_name)
            return int(getattr(collection, "points_count", 0) or 0)
        except Exception:
            return 0


class VectorStore:
    """
    Local FAISS-based vector store for semantic search.

    This implementation uses FAISS IndexFlatIP (inner product) for cosine similarity
    search with on-disk persistence. The index and metadata are stored as separate files
    to enable persistence across application restarts.

    Idempotent indexing is achieved by deleting existing document vectors before
    re-indexing, preventing duplicate entries for the same document.
    """

    def __init__(
        self,
        index_directory: Path,
    ):
        """
        Initialize the vector store with a specified directory for index persistence.

        Args:
            index_directory: Directory path where index and metadata files are stored
        """
        self.index_directory = Path(
            index_directory
        )

        self.index_path = (
            self.index_directory
            / "cloudrag.index"
        )

        self.metadata_path = (
            self.index_directory
            / "metadata.json"
        )

        self.index_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index = None

        self.metadata = []

        self._load()

    def _load(self):
        """
        Load the FAISS index and metadata from disk if they exist.

        This method is called during initialization to restore the vector store
        state from previous runs. If no index exists, the store starts empty.
        """
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
        """
        Persist the FAISS index and metadata to disk.

        This method writes the current index state to cloudrag.index and
        the metadata list to metadata.json, ensuring changes survive application restarts.
        """
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
        """
        Add chunks to the vector store. If the document already exists,
        delete old vectors first to ensure idempotent indexing.

        Idempotency is important because users may re-index the same document
        after corrections or to update the index. Without deduplication, the
        same content would appear multiple times in search results.

        Args:
            chunks: List of TextChunk objects with text and metadata
            embeddings: Array of embedding vectors corresponding to chunks
        """
        if not chunks:
            return

        # Check if document already exists and delete old vectors
        if chunks:
            document_id = chunks[0].document_id
            existing_doc_ids = {m["document_id"] for m in self.metadata}
            if document_id in existing_doc_ids:
                self.delete_document(document_id)

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
                    "page": chunk.page,  # Include page number for citations
                }
            )

        self._save()

    def delete_document(
        self,
        document_id: str,
    ):
        """
        Remove all chunks associated with a document from the vector store.

        This method reconstructs the index without the deleted document's vectors
        and updates the metadata accordingly. This is used when documents are
        deleted by users or during idempotent re-indexing.

        Args:
            document_id: The ID of the document to remove from the store
        """
        remaining_metadata = []

        remaining_vectors = []

        if self.index is not None:

            vectors = self.index.reconstruct_n(
                0,
                self.index.ntotal,
            )

            for index, metadata in enumerate(
                self.metadata
            ):

                if (
                    metadata["document_id"]
                    != document_id
                ):

                    remaining_metadata.append(
                        metadata
                    )

                    remaining_vectors.append(
                        vectors[index]
                    )

        self.metadata = remaining_metadata

        if remaining_vectors:

            matrix = np.asarray(
                remaining_vectors,
                dtype="float32",
            )

            dimension = matrix.shape[1]

            self.index = faiss.IndexFlatIP(
                dimension
            )

            self.index.add(matrix)

        else:

            self.index = None

            self.index_path.unlink(
                missing_ok=True
            )

        self._save()

    def search(
        self,
        query_embedding,
        top_k: int = 5,
        document_id: str | None = None,
    ):
        """
        Search for the most similar chunks to the query embedding.

        When document_id is specified, the search is restricted to chunks from
        that document only. This is useful for document-specific Q&A.

        Note: When a document filter is applied, we retrieve all vectors first
        and then filter post-search. This ensures correct behavior even when
        the best matching chunk from the selected document would otherwise
        fall below the global top_k threshold.

        Args:
            query_embedding: The embedding vector for the search query
            top_k: Maximum number of results to return
            document_id: Optional document ID to restrict search scope

        Returns:
            List of dictionaries containing chunk metadata and similarity scores
        """
        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        query_vector = np.asarray(
            query_embedding,
            dtype="float32",
        )

        # A document filter is applied after the exact FAISS search.  Asking
        # FAISS for every vector here keeps the selected-document behaviour
        # correct even when its best chunk would otherwise fall below top_k.
        result_count = self.index.ntotal if document_id else min(
            top_k, self.index.ntotal
        )
        scores, indices = (
            self.index.search(
                query_vector,
                result_count,
            )
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index < 0:
                continue

            metadata = self.metadata[
                index
            ]

            if document_id and metadata["document_id"] != document_id:
                continue

            results.append(
                {
                    **metadata,
                    "score": float(score),
                }
            )

            if len(results) >= top_k:
                break

        return results

    @property
    def size(self) -> int:
        """
        Return the total number of vectors in the index.

        Returns:
            Number of indexed chunks, or 0 if no index exists
        """
        if self.index is None:
            return 0

        return self.index.ntotal
