"""Accumulation tracking for rising tide pattern detection."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Union

from comprehension.schema import Comprehension
from .similarity import SimilarityMatch


@dataclass
class AccumulationHotspot:
    """A comprehension where structural similarity is accumulating.

    Hotspots are comprehensions that have connections to similar
    comprehensions across multiple domains. They are candidates
    for meta-comprehension crystallization (Phase 5).
    """

    comprehension_id: str
    domain_count: int  # How many different domains have similar comprehensions
    connection_count: int  # Total number of similarity edges pointing to this
    avg_similarity: float  # Average similarity of connections


class AccumulationTracker:
    """Track where structural similarity is accumulating across domains.

    Records similarity relationships between comprehensions and identifies
    hotspots where the same pattern appears across multiple domains.
    This enables "rising tide" detection for meta-comprehension.

    Thread safety: Each method opens/closes its own connection.
    """

    def __init__(self, db_path: Union[str, Path]):
        """Initialize accumulation tracker.

        Creates similarity_edges table if it doesn't exist.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a new database connection.

        Returns:
            sqlite3.Connection (no sqlite-vec needed for edges table).
        """
        return sqlite3.connect(self._db_path)

    def _ensure_schema(self) -> None:
        """Ensure similarity_edges table exists."""
        conn = self._connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS similarity_edges (
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    similarity REAL NOT NULL,
                    source_domain TEXT NOT NULL,
                    target_domain TEXT NOT NULL,
                    created TEXT NOT NULL,
                    PRIMARY KEY (source_id, target_id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_similarity_target
                ON similarity_edges(target_id, similarity)
            """)
            conn.commit()
        finally:
            conn.close()

    def record_similarity(
        self,
        source_id: str,
        target_id: str,
        similarity: float,
        source_domain: str,
        target_domain: str
    ) -> None:
        """Record a similarity relationship between two comprehensions.

        Creates or updates an edge in the similarity graph.
        Uses INSERT OR REPLACE for upsert semantics.

        Args:
            source_id: ID of the querying comprehension.
            target_id: ID of the similar comprehension.
            similarity: Similarity score (0-1).
            source_domain: Domain of the source comprehension.
            target_domain: Domain of the target comprehension.
        """
        created = datetime.now(timezone.utc).isoformat()

        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO similarity_edges
                (source_id, target_id, similarity, source_domain, target_domain, created)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source_id, target_id, similarity, source_domain, target_domain, created)
            )
            conn.commit()
        finally:
            conn.close()

    def record_matches(
        self,
        source: Comprehension,
        matches: List[SimilarityMatch]
    ) -> None:
        """Record all similarity matches from a reminds_me_of query.

        Convenience method that records multiple edges at once.

        Args:
            source: The comprehension that was queried.
            matches: List of SimilarityMatch results.
        """
        for match in matches:
            self.record_similarity(
                source_id=source.id,
                target_id=match.comprehension_id,
                similarity=match.similarity,
                source_domain=source.domain,
                target_domain=match.domain
            )

    def get_connections(
        self,
        comprehension_id: str
    ) -> List[Tuple[str, str, float]]:
        """Get all connections for a comprehension.

        Returns edges where this comprehension is either source OR target.

        Args:
            comprehension_id: ID of the comprehension.

        Returns:
            List of (other_id, other_domain, similarity) tuples.
        """
        conn = self._connect()
        try:
            # Get outgoing edges (this comprehension as source)
            cursor = conn.execute(
                """
                SELECT target_id, target_domain, similarity
                FROM similarity_edges
                WHERE source_id = ?
                """,
                (comprehension_id,)
            )
            results = [(row[0], row[1], row[2]) for row in cursor.fetchall()]

            # Get incoming edges (this comprehension as target)
            cursor = conn.execute(
                """
                SELECT source_id, source_domain, similarity
                FROM similarity_edges
                WHERE target_id = ?
                """,
                (comprehension_id,)
            )
            results.extend([(row[0], row[1], row[2]) for row in cursor.fetchall()])

            return results
        finally:
            conn.close()

    def get_hotspots(
        self,
        min_domains: int = 2,
        min_connections: int = 3
    ) -> List[AccumulationHotspot]:
        """Find comprehensions with cross-domain similarity accumulation.

        Identifies hotspots where a comprehension has connections to
        similar comprehensions across multiple domains. These are
        candidates for meta-comprehension (Phase 5).

        Args:
            min_domains: Minimum number of distinct source domains.
            min_connections: Minimum number of incoming edges.

        Returns:
            List of AccumulationHotspot objects, ordered by domain count then avg similarity.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                SELECT
                    target_id,
                    COUNT(DISTINCT source_domain) as domain_count,
                    COUNT(*) as connection_count,
                    AVG(similarity) as avg_similarity
                FROM similarity_edges
                GROUP BY target_id
                HAVING COUNT(DISTINCT source_domain) >= ? AND COUNT(*) >= ?
                ORDER BY domain_count DESC, avg_similarity DESC
                """,
                (min_domains, min_connections)
            )

            return [
                AccumulationHotspot(
                    comprehension_id=row[0],
                    domain_count=row[1],
                    connection_count=row[2],
                    avg_similarity=row[3]
                )
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def remove_edges(self, comprehension_id: str) -> int:
        """Remove all edges involving a comprehension.

        Removes edges where this comprehension is source OR target.
        Called when a comprehension is deleted.

        Args:
            comprehension_id: ID of the comprehension.

        Returns:
            Number of edges removed.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                DELETE FROM similarity_edges
                WHERE source_id = ? OR target_id = ?
                """,
                (comprehension_id, comprehension_id)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
