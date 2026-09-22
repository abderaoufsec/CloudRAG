from collections import OrderedDict
from pathlib import Path

from app.rag.chunker import create_chunks
from app.rag.embeddings import embed_query, embed_texts
from app.providers.factory import get_llm_provider
from app.rag.vector_store import QdrantVectorStore, VectorStore
from app.config import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INDEX_DIRECTORY = PROJECT_ROOT / "data" / "index"


class RAGPipeline:
    """
    Main Retrieval-Augmented Generation pipeline for CloudRAG.

    This class orchestrates document indexing, vector search, context construction,
    and LLM-based answer generation. It manages a local FAISS or Qdrant vector store,
    implements search caching with invalidation, and enforces retrieval quality thresholds.

    The pipeline treats all document content as untrusted evidence and constrains
    the LLM to answer only using retrieved context to ensure grounded responses.
    """

    def __init__(self):
        """
        Initialize the RAG pipeline with the configured vector store.

        The vector store is selected based on the VECTOR_STORE environment variable:
        - 'qdrant': Uses Qdrant Cloud for remote vector storage
        - Any other value: Uses local FAISS index (default)

        A bounded LRU cache is initialized for repeated query optimization.
        """
        settings = get_settings()
        if settings.vector_store.lower() == "qdrant":
            self.vector_store = QdrantVectorStore(INDEX_DIRECTORY)
        else:
            self.vector_store = VectorStore(INDEX_DIRECTORY)
        self._search_cache = OrderedDict()
        self._max_cache_entries = 128

    def _ensure_cache(self):
        """
        Ensure the search cache is initialized with default configuration.

        This is a defensive check to handle cases where the cache might not
        be properly initialized during deserialization or edge cases.
        """
        if not hasattr(self, "_search_cache"):
            self._search_cache = OrderedDict()
        if not hasattr(self, "_max_cache_entries"):
            self._max_cache_entries = 128

    def index_document(
        self,
        document_id: str,
        text: str,
        page_mapping: list[int] | None = None,
    ):
        """
        Index a document by chunking, embedding, and storing vectors.
        Invalidates cache entries related to this document to prevent stale results.
        """
        chunks = create_chunks(
            text=text,
            document_id=document_id,
            page_mapping=page_mapping,
        )

        if not chunks:
            return {
                "document_id": document_id,
                "chunks": 0,
            }

        embeddings = embed_texts(
            [chunk.text for chunk in chunks]
        )

        self.vector_store.add_chunks(
            chunks,
            embeddings,
        )

        # Invalidate cache entries that might reference this document
        self._invalidate_document_cache(document_id)

        return {
            "document_id": document_id,
            "chunks": len(chunks),
            "vector_store_size": self.vector_store.size,
        }

    def search(
        self,
        query: str,
        top_k: int = 5,
        document_id: str | None = None,
    ):
        """
        Search for document chunks relevant to the query using semantic similarity.

        Results are cached to optimize repeated queries. The cache is keyed by
        (query, top_k, document_id) and uses an LRU eviction policy when full.

        Args:
            query: The user's question or search text
            top_k: Maximum number of results to return
            document_id: Optional document ID to restrict search to a specific document

        Returns:
            List of retrieval results containing chunk text, scores, and metadata
        """
        self._ensure_cache()
        cache_key = (query, top_k, document_id)
        if cache_key in self._search_cache:
            self._search_cache.move_to_end(cache_key)
            return list(self._search_cache[cache_key])

        query_embedding = embed_query(query)
        results = self.vector_store.search(
            query_embedding,
            top_k=top_k,
            document_id=document_id,
        )

        self._search_cache[cache_key] = list(results)
        self._search_cache.move_to_end(cache_key)
        if len(self._search_cache) > self._max_cache_entries:
            self._search_cache.popitem(last=False)

        return list(results)

    def _invalidate_document_cache(self, document_id: str):
        """
        Invalidate all cache entries that reference a specific document.

        This ensures stale results are never returned after document changes.
        Removes both scoped queries (document_id matches) and global queries
        (document_id is None) that might have returned results from this document.

        Args:
            document_id: The ID of the document that was changed or deleted
        """
        self._ensure_cache()
        keys_to_remove = []
        for key in self._search_cache.keys():
            # key is (query, top_k, document_id)
            # Remove if query specifically targets this document
            if key[2] == document_id:
                keys_to_remove.append(key)
            # Also remove global queries (document_id is None) since they
            # might have returned results from the changed document
            elif key[2] is None:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._search_cache[key]



    def delete_document(
        self,
        document_id: str,
    ):
        """
        Delete a document from the vector store and invalidate related cache entries.

        This removes all chunks associated with the document and clears any cached
        search results that might reference the deleted document.

        Args:
            document_id: The ID of the document to delete
        """
        self.vector_store.delete_document(
            document_id
        )
        self._invalidate_document_cache(document_id)

    def ask(
        self,
        question: str,
        top_k: int = 5,
        document_id: str | None = None,
    ):
        """
        Generate a grounded answer to a question using retrieved document context.

        This method performs semantic search, filters results by relevance score,
        constructs a context window within character limits, and calls the LLM
        with explicit instructions to answer only using the provided context.

        If no relevant chunks are found above the minimum score threshold,
        the system abstains from answering rather than hallucinating.

        Args:
            question: The user's question
            top_k: Maximum number of chunks to retrieve
            document_id: Optional document ID to restrict search

        Returns:
            Dictionary containing:
            - answer: The LLM-generated response (or abstention message)
            - sources: List of source metadata (document_id, chunk_id, score, page, filename)
        """
        results = self.search(
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        settings = get_settings()

        # Filter out low-confidence results to avoid calling LLM with weak context
        results = [
            result
            for result in results
            if result["score"] >= settings.min_retrieval_score
        ]

        if not results:
            return {
                "answer": (
                    "I could not find relevant information "
                    "in the indexed documents."
                ),
                "sources": [],
            }

        context_parts = []
        context_length = 0

        sources = []

        for result in results:

            context_part = (
                f"[Source: {result['document_id']} | "
                f"Chunk: {result['chunk_index']}]\n"
                f"{result['text']}"
            )

            remaining = (
                settings.max_rag_context_characters
                - context_length
            )
            if remaining <= 0:
                break

            context_parts.append(context_part[:remaining])
            context_length += len(context_parts[-1])

            sources.append(
              {
               "document_id": result["document_id"],
               "chunk_id": result["chunk_id"],
               "chunk_index": result["chunk_index"],
               "score": result["score"],
               "page": result.get("page"),  # Include page number for citations
               "filename": result.get(
               "filename",
                 result["document_id"],
                  ),
                   }
              )

        context = "\n\n---\n\n".join(
            context_parts
        )

        answer = get_llm_provider().generate(
            question=question,
            context=context,
        )



        return {
            "answer": answer,
            "sources": sources,
        }


rag_pipeline = RAGPipeline()
