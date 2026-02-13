"""SQLite repository for comprehension persistence."""

import sqlite3
from pathlib import Path
from typing import Optional, Union

from comprehension.schema import Comprehension
from .migrations import ensure_schema


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
