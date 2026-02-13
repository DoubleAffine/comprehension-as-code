"""Schema creation and versioning for comprehension store."""

import sqlite3
from typing import Optional


SCHEMA_VERSION = 2  # v2: Added FTS5 virtual table for topic search


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
        _apply_v2_fts5(conn)
        _set_schema_version(conn, SCHEMA_VERSION)
    elif current_version < SCHEMA_VERSION:
        # Apply migrations incrementally
        if current_version < 2:
            _apply_v2_fts5(conn)
            _set_schema_version(conn, 2)

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


def _check_fts5_available(conn: sqlite3.Connection) -> bool:
    """Check if FTS5 extension is available."""
    try:
        conn.execute("SELECT fts5(?)", ("test",))
        return True
    except sqlite3.OperationalError:
        # FTS5 not available via function, try creating a temp table
        try:
            conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_test "
                "USING fts5(content)"
            )
            conn.execute("DROP TABLE IF EXISTS _fts5_test")
            return True
        except sqlite3.OperationalError:
            return False


def _apply_v2_fts5(conn: sqlite3.Connection) -> None:
    """Apply version 2 schema: FTS5 full-text search.

    Creates FTS5 virtual table for topic search with Porter stemmer.
    Adds triggers to keep FTS5 index in sync with comprehensions table.
    """
    if not _check_fts5_available(conn):
        # FTS5 not available - skip (graceful degradation)
        # find_by_topic will fall back to LIKE queries
        return

    # FTS5 virtual table for full-text search on topic
    # Uses Porter stemmer for word stemming (e.g., "learning" matches "learn")
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS comprehensions_fts
        USING fts5(
            id,
            topic,
            domain,
            content='comprehensions',
            content_rowid='rowid',
            tokenize='porter unicode61'
        )
    """)

    # Trigger: INSERT - add to FTS index
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS comprehensions_fts_insert
        AFTER INSERT ON comprehensions
        BEGIN
            INSERT INTO comprehensions_fts(rowid, id, topic, domain)
            VALUES (NEW.rowid, NEW.id, NEW.topic, NEW.domain);
        END
    """)

    # Trigger: DELETE - remove from FTS index
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS comprehensions_fts_delete
        AFTER DELETE ON comprehensions
        BEGIN
            INSERT INTO comprehensions_fts(comprehensions_fts, rowid, id, topic, domain)
            VALUES ('delete', OLD.rowid, OLD.id, OLD.topic, OLD.domain);
        END
    """)

    # Trigger: UPDATE - update FTS index
    # FTS5 update requires delete then insert
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS comprehensions_fts_update
        AFTER UPDATE ON comprehensions
        BEGIN
            INSERT INTO comprehensions_fts(comprehensions_fts, rowid, id, topic, domain)
            VALUES ('delete', OLD.rowid, OLD.id, OLD.topic, OLD.domain);
            INSERT INTO comprehensions_fts(rowid, id, topic, domain)
            VALUES (NEW.rowid, NEW.id, NEW.topic, NEW.domain);
        END
    """)
