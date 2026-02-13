"""SQLite repository for comprehension persistence."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Union

from comprehension.schema import Comprehension, ConfidenceLevel
from .migrations import ensure_schema
from .queries import build_filter_query, get_confidence_values_at_or_above


class SQLiteComprehensionRepository:
    """SQLite-backed repository for comprehension storage.

    Provides CRUD operations for Comprehension objects, storing them
    in SQLite with indexed fields for efficient queries and the full
    model serialized as JSON for complete fidelity.

    Thread safety: Each method opens/closes its own connection.
    Callers should handle synchronization for concurrent access.
    """

    def __init__(self, db_path: Union[str, Path]):
        """Initialize repository with database path.

        Creates database and schema if they don't exist.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Ensure database schema exists."""
        conn = sqlite3.connect(self._db_path)
        try:
            ensure_schema(conn)
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return sqlite3.connect(self._db_path)

    def add(self, comprehension: Comprehension) -> None:
        """Add or update a comprehension in the store.

        Uses INSERT OR REPLACE for upsert semantics.
        Extracts indexed fields and stores full model as JSON.

        Args:
            comprehension: The comprehension to store
        """
        conn = self._connect()
        try:
            # Extract indexed fields
            # confidence stored as string value (e.g., "high", "medium")
            confidence_value = comprehension.posterior.confidence.value

            conn.execute(
                """
                INSERT OR REPLACE INTO comprehensions
                (id, domain, topic, confidence, created, updated, version, verified, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comprehension.id,
                    comprehension.domain,
                    comprehension.topic,
                    confidence_value,
                    comprehension.created.isoformat(),
                    comprehension.updated.isoformat(),
                    comprehension.version,
                    1 if comprehension.verified else 0,
                    comprehension.model_dump_json(),
                )
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, id: str) -> Optional[Comprehension]:
        """Retrieve a comprehension by ID.

        Args:
            id: The comprehension ID to look up

        Returns:
            The Comprehension if found, None otherwise
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT data FROM comprehensions WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return Comprehension.model_validate_json(row[0])
        finally:
            conn.close()

    def delete(self, id: str) -> bool:
        """Delete a comprehension by ID.

        Args:
            id: The comprehension ID to delete

        Returns:
            True if a comprehension was deleted, False if not found
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM comprehensions WHERE id = ?",
                (id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def count(self) -> int:
        """Get total count of comprehensions in store.

        Returns:
            Number of comprehensions stored
        """
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM comprehensions")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _has_fts5(self, conn: sqlite3.Connection) -> bool:
        """Check if FTS5 table exists."""
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='comprehensions_fts'"
        )
        return cursor.fetchone() is not None

    def _rows_to_comprehensions(self, rows: list) -> List[Comprehension]:
        """Convert database rows (data column) to Comprehension objects."""
        return [Comprehension.model_validate_json(row[0]) for row in rows]

    def find_by_domain(self, domain: str) -> List[Comprehension]:
        """Find all comprehensions in a domain.

        Args:
            domain: Domain to filter by (exact match)

        Returns:
            List of comprehensions ordered by updated DESC
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT data FROM comprehensions WHERE domain = ? ORDER BY updated DESC",
                (domain,)
            )
            return self._rows_to_comprehensions(cursor.fetchall())
        finally:
            conn.close()

    def find_by_topic(self, query: str, limit: int = 10) -> List[Comprehension]:
        """Search comprehensions by topic using full-text search.

        Uses FTS5 with BM25 ranking when available, falls back to
        LIKE queries otherwise.

        Args:
            query: Search query (supports FTS5 syntax when available)
            limit: Maximum number of results (default 10)

        Returns:
            List of matching comprehensions ranked by relevance
        """
        conn = self._connect()
        try:
            if self._has_fts5(conn):
                # Use FTS5 with BM25 ranking
                cursor = conn.execute(
                    """
                    SELECT c.data
                    FROM comprehensions c
                    JOIN comprehensions_fts fts ON c.id = fts.id
                    WHERE comprehensions_fts MATCH ?
                    ORDER BY bm25(comprehensions_fts)
                    LIMIT ?
                    """,
                    (query, limit)
                )
            else:
                # Fallback to LIKE query
                cursor = conn.execute(
                    """
                    SELECT data FROM comprehensions
                    WHERE topic LIKE ?
                    ORDER BY updated DESC
                    LIMIT ?
                    """,
                    (f"%{query}%", limit)
                )
            return self._rows_to_comprehensions(cursor.fetchall())
        finally:
            conn.close()

    def find_by_confidence(
        self, min_confidence: ConfidenceLevel
    ) -> List[Comprehension]:
        """Find comprehensions at or above a confidence level.

        Args:
            min_confidence: Minimum confidence level to include

        Returns:
            List of comprehensions ordered by updated DESC
        """
        conn = self._connect()
        try:
            values = get_confidence_values_at_or_above(min_confidence)
            placeholders = ", ".join("?" for _ in values)
            cursor = conn.execute(
                f"SELECT data FROM comprehensions WHERE confidence IN ({placeholders}) ORDER BY updated DESC",
                values
            )
            return self._rows_to_comprehensions(cursor.fetchall())
        finally:
            conn.close()

    def find_recent(self, limit: int = 10) -> List[Comprehension]:
        """Find most recently updated comprehensions.

        Args:
            limit: Maximum number of results (default 10)

        Returns:
            List of comprehensions ordered by updated DESC
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT data FROM comprehensions ORDER BY updated DESC LIMIT ?",
                (limit,)
            )
            return self._rows_to_comprehensions(cursor.fetchall())
        finally:
            conn.close()

    def find(
        self,
        domain: Optional[str] = None,
        min_confidence: Optional[ConfidenceLevel] = None,
        topic_query: Optional[str] = None,
        limit: int = 20,
    ) -> List[Comprehension]:
        """Find comprehensions with combined filters.

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
        conn = self._connect()
        try:
            # If topic_query is provided and FTS5 is available, use FTS5 join
            if topic_query and self._has_fts5(conn):
                return self._find_with_fts(
                    conn, domain, min_confidence, topic_query, limit
                )
            else:
                # Use regular query builder
                query, params = build_filter_query(
                    domain=domain,
                    min_confidence=min_confidence,
                    limit=limit,
                )
                cursor = conn.execute(query, params)
                return self._rows_to_comprehensions(cursor.fetchall())
        finally:
            conn.close()

    def _find_with_fts(
        self,
        conn: sqlite3.Connection,
        domain: Optional[str],
        min_confidence: Optional[ConfidenceLevel],
        topic_query: str,
        limit: int,
    ) -> List[Comprehension]:
        """Find with FTS5 topic search and optional filters."""
        conditions = ["comprehensions_fts MATCH ?"]
        params: list = [topic_query]

        if domain is not None:
            conditions.append("c.domain = ?")
            params.append(domain)

        if min_confidence is not None:
            values = get_confidence_values_at_or_above(min_confidence)
            placeholders = ", ".join("?" for _ in values)
            conditions.append(f"c.confidence IN ({placeholders})")
            params.extend(values)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        cursor = conn.execute(
            f"""
            SELECT c.data
            FROM comprehensions c
            JOIN comprehensions_fts fts ON c.id = fts.id
            WHERE {where_clause}
            ORDER BY bm25(comprehensions_fts)
            LIMIT ?
            """,
            params
        )
        return self._rows_to_comprehensions(cursor.fetchall())
