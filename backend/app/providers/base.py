from abc import ABC, abstractmethod


class LLMProviderError(RuntimeError):
    """Raised when a configured LLM provider cannot generate an answer."""


class LLMProvider(ABC):
    """Provider boundary used by the RAG pipeline after retrieval."""

    @abstractmethod
    def generate(self, *, question: str, context: str) -> str:
        """Generate a grounded answer from retrieved document context."""
