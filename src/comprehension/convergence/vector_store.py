"""Vector storage using sqlite-vec for KNN similarity search."""

import sqlite3
import struct
from pathlib import Path
from typing import List, Tuple, Union

import numpy as np
import sqlite_vec


class VectorStore:
    """SQLite-vec backed vector storage for comprehension embeddings.

    Stores 384-dimensional vectors in a sqlite-vec virtual table,
    enabling efficient KNN queries for similarity search.

    Thread safety: Each method opens/closes its own connection.
    Callers should handle synchronization for concurrent access.
    """

    def __init__(self, db_path: Union[str, Path]):
        """Initialize vector store with database path.

        Creates database and schema if they don't exist.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Create a new database connection with sqlite-vec loaded.

        Returns:
            sqlite3.Connection with vec0 extension loaded.
        """
        conn = sqlite3.connect(self._db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn

    def _ensure_schema(self) -> None:
        """Ensure vector table and ID mapping exist."""
        conn = self._connect()
        try:
            # Virtual table for vector storage (rowid-based)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS comprehension_vectors
                USING vec0(embedding float[384])
            """)

            # Mapping table: rowid -> comprehension_id
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_id_map (
                    rowid INTEGER PRIMARY KEY,
                    comprehension_id TEXT UNIQUE NOT NULL
                )
            """)

            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _serialize(vector: np.ndarray) -> bytes:
        """Convert numpy array to sqlite-vec binary format.

        Args:
            vector: 384-dimensional numpy array.

        Returns:
            Binary representation for sqlite-vec.
        """
        return struct.pack("%sf" % len(vector), *vector.tolist())

    def _get_rowid(self, comprehension_id: str) -> int:
        """Generate stable rowid from comprehension ID.

        Uses hash to create a positive 32-bit integer rowid.

        Args:
            comprehension_id: Comprehension identifier.

        Returns:
            Positive integer rowid.
        """
        return hash(comprehension_id) & 0x7FFFFFFF

    def add(self, comprehension_id: str, embedding: np.ndarray) -> None:
        """Add or update a comprehension embedding.

        Uses INSERT OR REPLACE for upsert semantics.

        Args:
            comprehension_id: Unique identifier for the comprehension.
            embedding: 384-dimensional embedding vector.
        """
        rowid = self._get_rowid(comprehension_id)
        serialized = self._serialize(embedding)

        conn = self._connect()
        try:
            # Update vector (delete + insert for virtual table)
            conn.execute(
                "DELETE FROM comprehension_vectors WHERE rowid = ?",
                (rowid,)
            )
            conn.execute(
                "INSERT INTO comprehension_vectors(rowid, embedding) VALUES (?, ?)",
                (rowid, serialized)
            )

            # Update ID mapping
            conn.execute(
                "INSERT OR REPLACE INTO vector_id_map(rowid, comprehension_id) VALUES (?, ?)",
                (rowid, comprehension_id)
            )

            conn.commit()
        finally:
            conn.close()

    def remove(self, comprehension_id: str) -> bool:
        """Remove a comprehension embedding.

        Args:
            comprehension_id: Comprehension ID to remove.

        Returns:
            True if removed, False if not found.
        """
        rowid = self._get_rowid(comprehension_id)

        conn = self._connect()
        try:
            # Check if exists
            cursor = conn.execute(
                "SELECT 1 FROM vector_id_map WHERE rowid = ?",
                (rowid,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                conn.execute(
                    "DELETE FROM comprehension_vectors WHERE rowid = ?",
                    (rowid,)
                )
                conn.execute(
                    "DELETE FROM vector_id_map WHERE rowid = ?",
                    (rowid,)
                )
                conn.commit()

            return exists
        finally:
            conn.close()

    def query_knn(
        self, embedding: np.ndarray, limit: int = 5
    ) -> List[Tuple[str, float]]:
        """Query for nearest neighbors by embedding similarity.

        Returns comprehension IDs ranked by distance (closest first).
        Distance is cosine distance (0 = identical, 2 = opposite).

        Args:
            embedding: Query embedding (384-dimensional).
            limit: Maximum number of results to return.

        Returns:
            List of (comprehension_id, distance) tuples, ordered by distance.
        """
        serialized = self._serialize(embedding)

        conn = self._connect()
        try:
            # sqlite-vec requires k = ? in WHERE clause for KNN queries
            # First get the rowids and distances from the vector table
            cursor = conn.execute(
                """
                SELECT rowid, distance
                FROM comprehension_vectors
                WHERE embedding MATCH ? AND k = ?
                ORDER BY distance
                """,
                (serialized, limit)
            )

            # Then map rowids to comprehension IDs
            results = []
            for rowid, distance in cursor.fetchall():
                id_cursor = conn.execute(
                    "SELECT comprehension_id FROM vector_id_map WHERE rowid = ?",
                    (rowid,)
                )
                row = id_cursor.fetchone()
                if row:
                    results.append((row[0], distance))

            return results
        finally:
            conn.close()

    def count(self) -> int:
        """Get total number of stored vectors.

        Returns:
            Number of vectors in the store.
        """
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM vector_id_map")
            return cursor.fetchone()[0]
        finally:
            conn.close()
