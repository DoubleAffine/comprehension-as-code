"""BeliefStore: Main interface for belief persistence.

This is the public API for the belief store system. It provides a unified
interface for saving, retrieving, and querying comprehensions, while
managing observation references for memory-efficient storage.
"""

from pathlib import Path
from typing import List, Optional, Union

from comprehension.schema import Comprehension, ConfidenceLevel
from .repository import SQLiteComprehensionRepository
from .observation_index import ObservationIndex


class BeliefStore:
    """Main interface for belief persistence.

    Provides a unified API for:
    - Saving and updating comprehensions
    - Querying by domain, topic, confidence, recency
    - Managing observation references

    This is the public interface; repository/index are implementation details.

    Example:
        store = BeliefStore("beliefs.db")
        store.save(comprehension)
        results = store.find(domain="api", min_confidence=ConfidenceLevel.MEDIUM)
    """

    def __init__(self, db_path: Union[str, Path]):
        """Initialize belief store with SQLite database path.

        Creates database and schema if they don't exist.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = Path(db_path)
        self._repository = SQLiteComprehensionRepository(db_path)
        self._observation_index = ObservationIndex(db_path)

    # Persistence

    def save(self, comprehension: Comprehension) -> None:
        """Save or update a comprehension.

        Also updates observation index with any new observation references.
        If comprehension already exists, it will be replaced (upsert).

        Args:
            comprehension: The comprehension to store
        """
        self._repository.add(comprehension)

        # Update observation index with references
        for obs_id in comprehension.observations:
            self._observation_index.record_reference(obs_id, comprehension.id)

    def get(self, comprehension_id: str) -> Optional[Comprehension]:
        """Get comprehension by ID.

        Args:
            comprehension_id: The unique identifier of the comprehension

        Returns:
            The Comprehension if found, None otherwise
        """
        return self._repository.get(comprehension_id)

    def delete(self, comprehension_id: str) -> bool:
        """Delete comprehension by ID.

        Also removes observation references from the index.

        Args:
            comprehension_id: The unique identifier to delete

        Returns:
            True if a comprehension was deleted, False if not found
        """
        # Remove observation references first
        self._observation_index.remove_references_for_comprehension(comprehension_id)

        return self._repository.delete(comprehension_id)

    # Retrieval

    def find_by_domain(self, domain: str) -> List[Comprehension]:
        """Find all comprehensions in a domain.

        Args:
            domain: Domain to filter by (exact match)

        Returns:
            List of comprehensions ordered by updated DESC
        """
        return self._repository.find_by_domain(domain)

    def find_by_topic(self, query: str, limit: int = 10) -> List[Comprehension]:
        """Full-text search on topic.

        Uses FTS5 with BM25 ranking when available, falls back to
        LIKE queries otherwise.

        Args:
            query: Search query (supports FTS5 syntax when available)
            limit: Maximum number of results (default 10)

        Returns:
            List of matching comprehensions ranked by relevance
        """
        return self._repository.find_by_topic(query, limit)

    def find_by_confidence(
        self, min_confidence: ConfidenceLevel
    ) -> List[Comprehension]:
        """Find comprehensions at or above confidence level.

        Args:
            min_confidence: Minimum confidence level to include

        Returns:
            List of comprehensions ordered by updated DESC
        """
        return self._repository.find_by_confidence(min_confidence)

    def find_recent(self, limit: int = 10) -> List[Comprehension]:
        """Get most recently updated comprehensions.

        Args:
            limit: Maximum number of results (default 10)

        Returns:
            List of comprehensions ordered by updated DESC
        """
        return self._repository.find_recent(limit)

    def find(
        self,
        domain: Optional[str] = None,
        min_confidence: Optional[ConfidenceLevel] = None,
        topic_query: Optional[str] = None,
        limit: int = 20,
    ) -> List[Comprehension]:
        """Combined query with multiple filters.

        All filters are optional; when None, that dimension is not filtered.
        Results are always ordered by updated DESC.

        Args:
            domain: Optional domain to filter by (exact match)
            min_confidence: Optional minimum confidence level
            topic_query: Optional FTS5 search query
            limit: Maximum number of results (default 20)

        Returns:
            List of matching comprehensions
        """
        return self._repository.find(
            domain=domain,
            min_confidence=min_confidence,
            topic_query=topic_query,
            limit=limit,
        )

    # Observation management

    def get_observation_index(self) -> ObservationIndex:
        """Access observation index for pruning operations.

        Returns:
            The ObservationIndex instance for managing observation references
        """
        return self._observation_index

    # Stats

    def stats(self) -> dict:
        """Get store statistics.

        Returns:
            Dict with counts: comprehension_count, domains, observation stats
        """
        comp_count = self._repository.count()
        obs_stats = self._observation_index.stats()

        return {
            "comprehension_count": comp_count,
            "observation_refs": obs_stats["total_refs"],
            "unique_observations": obs_stats["unique_observations"],
            "pruned_observations": obs_stats["pruned_count"],
        }
