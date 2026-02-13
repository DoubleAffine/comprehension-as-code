"""Similarity finder for cross-domain comprehension matching."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

from comprehension.schema import Comprehension
from comprehension.store.repository import SQLiteComprehensionRepository
from .embedder import ComprehensionEmbedder
from .vector_store import VectorStore


@dataclass
class SimilarityMatch:
    """A comprehension that is structurally similar to a query.

    Represents a match from the "reminds me of" operation.
    Matches are always from a DIFFERENT domain than the query.
    """

    comprehension_id: str
    domain: str
    similarity: float  # 0-1, higher is more similar


class SimilarityFinder:
    """Find comprehensions with similar structural patterns across domains.

    Implements the "reminds me of" operation: given a comprehension, find
    other comprehensions from DIFFERENT domains that have similar belief
    transformation patterns.

    Thread safety: Uses connection-per-operation pattern from VectorStore
    and SQLiteComprehensionRepository.
    """

    def __init__(
        self,
        db_path: Union[str, Path],
        embedder: Optional[ComprehensionEmbedder] = None
    ):
        """Initialize similarity finder.

        Args:
            db_path: Path to SQLite database file.
            embedder: Optional embedder instance. Creates new one if not provided.
        """
        self._db_path = Path(db_path)
        self._embedder = embedder or ComprehensionEmbedder()
        self._vector_store = VectorStore(db_path)
        self._repository = SQLiteComprehensionRepository(db_path)

    def index(self, comprehension: Comprehension) -> None:
        """Add a comprehension to the similarity index.

        Embeds the comprehension and stores it in the vector store
        for future similarity queries.

        Args:
            comprehension: Comprehension to index.
        """
        embedding = self._embedder.embed(comprehension)
        self._vector_store.add(comprehension.id, embedding)

    def remove_index(self, comprehension_id: str) -> bool:
        """Remove a comprehension from the similarity index.

        Args:
            comprehension_id: ID of comprehension to remove.

        Returns:
            True if removed, False if not found.
        """
        return self._vector_store.remove(comprehension_id)

    def reminds_me_of(
        self,
        comprehension: Comprehension,
        limit: int = 5,
        min_similarity: float = 0.75
    ) -> List[SimilarityMatch]:
        """Find structurally similar comprehensions from OTHER domains.

        The core "reminds me of" operation. Given a comprehension, finds
        other comprehensions that have similar belief transformation patterns
        but come from DIFFERENT domains. Same-domain matches are excluded
        because we're looking for cross-domain structural similarity.

        Args:
            comprehension: Query comprehension.
            limit: Maximum number of results to return.
            min_similarity: Minimum similarity threshold (0-1). Default 0.75.

        Returns:
            List of SimilarityMatch objects, ordered by similarity (highest first).
            Only includes matches from domains different from the query.
        """
        # Embed the query comprehension
        embedding = self._embedder.embed(comprehension)

        # Over-fetch to allow for domain filtering
        # We'll fetch 3x the limit since some will be same-domain
        candidates = self._vector_store.query_knn(embedding, limit=limit * 3)

        # Filter and convert to SimilarityMatch
        matches: List[SimilarityMatch] = []
        for comp_id, distance in candidates:
            # Skip self
            if comp_id == comprehension.id:
                continue

            # Load the comprehension to get its domain
            other = self._repository.get(comp_id)
            if other is None:
                # Comprehension was deleted but vector remains
                continue

            # Skip same-domain matches (cross-domain only!)
            if other.domain == comprehension.domain:
                continue

            # Convert distance to similarity: similarity = 1 - distance
            # sqlite-vec uses cosine distance where 0 = identical
            similarity = 1.0 - distance

            # Apply similarity threshold
            if similarity < min_similarity:
                continue

            matches.append(SimilarityMatch(
                comprehension_id=comp_id,
                domain=other.domain,
                similarity=similarity
            ))

            # Stop if we have enough matches
            if len(matches) >= limit:
                break

        return matches

    def find_similar_to_id(
        self,
        comprehension_id: str,
        limit: int = 5,
        min_similarity: float = 0.75
    ) -> List[SimilarityMatch]:
        """Find similar comprehensions by ID.

        Convenience method that loads the comprehension first,
        then calls reminds_me_of.

        Args:
            comprehension_id: ID of comprehension to find matches for.
            limit: Maximum number of results.
            min_similarity: Minimum similarity threshold.

        Returns:
            List of SimilarityMatch objects, or empty list if ID not found.
        """
        comprehension = self._repository.get(comprehension_id)
        if comprehension is None:
            return []
        return self.reminds_me_of(comprehension, limit, min_similarity)
