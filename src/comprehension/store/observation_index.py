"""Observation index for tracking references and pruning status.

Key insight: Observations are ephemeral; comprehensions persist. This index
enables memory-efficient storage by tracking which observations have content
vs. have been pruned, while preserving references in comprehensions.

The comprehension.observations list retains IDs even after content is pruned.
This index enables safe pruning decisions.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set, Union

from comprehension.update.lifecycle import ObservationLifecycle


class ObservationIndex:
    """Tracks observation references for memory efficiency.

    Observations are ephemeral; comprehensions persist. This index tracks:
    1. Which comprehensions reference each observation (observation_id -> [comp_ids])
    2. Which observations still have content vs. have been pruned

    Key insight: comprehension.observations list retains IDs even after
    content is pruned. This index enables safe pruning decisions.
    """

    def __init__(self, db_path: Union[str, Path]):
        """Initialize observation index with database path.

        Uses the same SQLite database as the comprehension repository.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = Path(db_path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create observation index tables if they don't exist."""
        conn = sqlite3.connect(self._db_path)
        try:
            # Table for observation -> comprehension references
            conn.execute("""
                CREATE TABLE IF NOT EXISTS observation_refs (
                    observation_id TEXT NOT NULL,
                    comprehension_id TEXT NOT NULL,
                    PRIMARY KEY (observation_id, comprehension_id)
                )
            """)

            # Index for fast lookup by comprehension
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_observation_refs_comp
                ON observation_refs(comprehension_id)
            """)

            # Table for tracking pruned observations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS observation_pruned (
                    observation_id TEXT PRIMARY KEY,
                    pruned_at TEXT NOT NULL
                )
            """)

            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        """Get a new database connection."""
        return sqlite3.connect(self._db_path)

    def record_reference(self, observation_id: str, comprehension_id: str) -> None:
        """Record that a comprehension references this observation.

        Creates a link between an observation and a comprehension that uses it.
        Idempotent: calling multiple times with same pair has no effect.

        Args:
            observation_id: ID of the observation being referenced
            comprehension_id: ID of the comprehension referencing it
        """
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO observation_refs
                (observation_id, comprehension_id)
                VALUES (?, ?)
                """,
                (observation_id, comprehension_id)
            )
            conn.commit()
        finally:
            conn.close()

    def mark_content_pruned(self, observation_id: str) -> None:
        """Mark observation content as deleted (reference remains).

        After calling this, is_content_available() returns False.
        The comprehension.observations list still contains the ID,
        but the actual observation content has been deleted.

        Args:
            observation_id: ID of the observation whose content was deleted
        """
        conn = self._connect()
        try:
            pruned_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT OR REPLACE INTO observation_pruned
                (observation_id, pruned_at)
                VALUES (?, ?)
                """,
                (observation_id, pruned_at)
            )
            conn.commit()
        finally:
            conn.close()

    def is_content_available(self, observation_id: str) -> bool:
        """Check if observation content still exists.

        Returns True if content has NOT been pruned,
        False if content has been deleted.

        Args:
            observation_id: ID of the observation to check

        Returns:
            True if content available, False if pruned
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM observation_pruned WHERE observation_id = ?",
                (observation_id,)
            )
            return cursor.fetchone() is None
        finally:
            conn.close()

    def get_referencing_comprehensions(self, observation_id: str) -> List[str]:
        """Get comprehension IDs that reference this observation.

        Args:
            observation_id: ID of the observation

        Returns:
            List of comprehension IDs that reference this observation
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                SELECT comprehension_id FROM observation_refs
                WHERE observation_id = ?
                """,
                (observation_id,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_prunable(self, lifecycle: ObservationLifecycle) -> Set[str]:
        """Get observations safe to prune.

        Returns observation IDs that are:
        1. INCORPORATED in lifecycle (used by comprehension)
        2. Not already pruned

        Args:
            lifecycle: ObservationLifecycle from Phase 2

        Returns:
            Set of observation IDs whose content can be deleted
        """
        # Get incorporated observations from lifecycle
        incorporated = lifecycle.get_collectible()

        # Filter out already pruned observations
        conn = self._connect()
        try:
            if not incorporated:
                return set()

            # Get all already-pruned observation IDs
            cursor = conn.execute("SELECT observation_id FROM observation_pruned")
            pruned = {row[0] for row in cursor.fetchall()}

            # Return incorporated that haven't been pruned yet
            return incorporated - pruned
        finally:
            conn.close()

    def get_references_for_comprehension(self, comprehension_id: str) -> List[str]:
        """Get observation IDs referenced by a comprehension.

        Args:
            comprehension_id: ID of the comprehension

        Returns:
            List of observation IDs referenced by this comprehension
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                SELECT observation_id FROM observation_refs
                WHERE comprehension_id = ?
                """,
                (comprehension_id,)
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def remove_references_for_comprehension(self, comprehension_id: str) -> int:
        """Remove all observation references for a deleted comprehension.

        Args:
            comprehension_id: ID of the deleted comprehension

        Returns:
            Number of references removed
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM observation_refs WHERE comprehension_id = ?",
                (comprehension_id,)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def stats(self) -> dict:
        """Get observation index statistics.

        Returns:
            Dict with counts: total_refs, unique_observations, pruned_count
        """
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM observation_refs")
            total_refs = cursor.fetchone()[0]

            cursor = conn.execute(
                "SELECT COUNT(DISTINCT observation_id) FROM observation_refs"
            )
            unique_observations = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM observation_pruned")
            pruned_count = cursor.fetchone()[0]

            return {
                "total_refs": total_refs,
                "unique_observations": unique_observations,
                "pruned_count": pruned_count,
            }
        finally:
            conn.close()
