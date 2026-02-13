"""Convergence detection: semantic similarity and vector storage for comprehensions."""

from .embedder import ComprehensionEmbedder
from .vector_store import VectorStore

__all__ = ["ComprehensionEmbedder", "VectorStore"]
