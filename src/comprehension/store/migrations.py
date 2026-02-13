"""Schema creation and versioning for comprehension store."""

import sqlite3
from typing import Optional


SCHEMA_VERSION = 1


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they don't exist.

    Creates:
    - comprehensions table with indexed fields + JSON data blob
    - schema_version table for tracking migrations
    - Indexes on domain, confidence, updated for efficient queries
    """
    # Create schema version tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Check current schema version
    current_version = _get_schema_version(conn)

    if current_version is None:
        # Fresh database - apply full schema
        _apply_v1_schema(conn)
        _set_schema_version(conn, SCHEMA_VERSION)
    elif current_version < SCHEMA_VERSION:
        # Future: migration logic goes here
        # For now, we only have v1
        pass

    conn.commit()


def _get_schema_version(conn: sqlite3.Connection) -> Optional[int]:
    """Get current schema version from database."""
    cursor = conn.execute(
        "SELECT MAX(version) FROM schema_version"
    )
    row = cursor.fetchone()
    return row[0] if row and row[0] is not None else None


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Record schema version in database."""
    conn.execute(
        "INSERT INTO schema_version (version) VALUES (?)",
        (version,)
    )


def _apply_v1_schema(conn: sqlite3.Connection) -> None:
    """Apply version 1 schema: comprehensions table with indexes."""
    # Main comprehensions table
    # Indexed fields extracted for efficient queries
    # Full comprehension stored as JSON in data column
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comprehensions (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            topic TEXT NOT NULL,
            confidence TEXT NOT NULL,
            created TEXT NOT NULL,
            updated TEXT NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            verified INTEGER NOT NULL DEFAULT 0,
            data TEXT NOT NULL
        )
    """)

    # Index on domain for filtering by category
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_comprehensions_domain
        ON comprehensions(domain)
    """)

    # Index on confidence for filtering by certainty
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_comprehensions_confidence
        ON comprehensions(confidence)
    """)

    # Index on updated for recent comprehensions
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_comprehensions_updated
        ON comprehensions(updated)
    """)

    # Composite index for domain + confidence queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_comprehensions_domain_confidence
        ON comprehensions(domain, confidence)
    """)
