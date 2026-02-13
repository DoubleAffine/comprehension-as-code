"""Convergence detection: semantic similarity and vector storage for comprehensions."""

from .embedder import ComprehensionEmbedder
from .vector_store import VectorStore
from .similarity import SimilarityFinder, SimilarityMatch
from .accumulator import AccumulationTracker, AccumulationHotspot

__all__ = [
    "ComprehensionEmbedder",
    "VectorStore",
    "SimilarityFinder",
    "SimilarityMatch",
    "AccumulationTracker",
    "AccumulationHotspot",
]
