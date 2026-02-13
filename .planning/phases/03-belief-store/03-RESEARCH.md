# Phase 3: Belief Store - Research

**Researched:** 2026-02-13
**Domain:** Persistence layer, retrieval patterns, memory efficiency for AI agent belief states
**Confidence:** HIGH

## Summary

Phase 3 implements the persistence layer for comprehensions. The existing codebase (Phases 1-2) defines `Comprehension` and `Observation` Pydantic models with Bayesian structure and a lifecycle manager that tracks observation states. This phase adds: (1) a persistence layer that stores comprehensions to disk, (2) retrieval by multiple dimensions (domain, topic, confidence, recency), and (3) a memory model where storage grows with understanding, not evidence count.

The key architectural insight is that comprehensions are beliefs (posteriors), not evidence (observations). The existing `ObservationLifecycle` from Phase 2 already tracks which observations are "collectible" after incorporation. Phase 3 extends this by persisting comprehensions while allowing observation content to be pruned. Observation references remain in `comprehension.observations` list, but actual observation files/records can be garbage collected.

**Primary recommendation:** Use SQLite with FTS5 for persistence and retrieval. Store comprehensions as JSON in a structured table with indexed columns for domain, topic, confidence, and updated timestamp. Avoid premature optimization with vector databases - the scale requirements (hundreds to low thousands of comprehensions) don't justify the complexity. Hybrid search with vectors can be added later when semantic retrieval becomes necessary.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **sqlite3** | stdlib | Primary persistence | Zero-config, built into Python, ACID compliant, sufficient for belief store scale |
| **Pydantic** | 2.x | Schema validation, serialization | Already in use; `model_dump_json()` for storage, `model_validate_json()` for retrieval |
| **python-frontmatter** | 1.x | Markdown file parsing | Already in pyproject.toml; for optional human-readable comprehension export |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **sqlite-utils** | 3.x | SQLite convenience wrapper | Simplifies table creation, JSON columns, querying; used by pydantic-sqlite |
| **sqlite-vec** | 0.1.6+ | Vector search extension | Only if semantic retrieval needed in future; not required for Phase 3 |
| **ChromaDB** | 1.5.0 | Vector database | Alternative to sqlite-vec if full semantic search needed; adds dependency |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite | ChromaDB | ChromaDB adds semantic search but adds dependency and complexity; overkill for structured belief retrieval |
| Raw SQL | SQLModel/SQLAlchemy | ORM adds abstraction but comprehension queries are simple enough that raw SQL is clearer |
| JSON files | SQLite | Files are simpler but lack query capability for confidence/recency filtering |
| pydantic-sqlite | Custom SQLite | pydantic-sqlite auto-handles Pydantic models but less control over schema design |

**Installation:**
```bash
# Already in pyproject.toml
pip install pydantic pyyaml python-frontmatter

# Add for Phase 3
pip install sqlite-utils
```

## Architecture Patterns

### Recommended Project Structure
```
src/comprehension/
|-- store/                    # NEW: Phase 3
|   |-- __init__.py
|   |-- belief_store.py       # BeliefStore class - main interface
|   |-- repository.py         # Repository pattern for SQLite operations
|   |-- queries.py            # Query builders for retrieval
|   |-- migrations.py         # Schema version management
|-- schema/                   # EXISTING: Phase 1
|   |-- comprehension.py
|   |-- observation.py
|   |-- confidence.py
|-- update/                   # EXISTING: Phase 2
|   |-- bayesian_update.py
|   |-- lifecycle.py
|   |-- confidence_rules.py
```

### Pattern 1: Repository Pattern for Persistence
**What:** Abstraction layer between domain models and database operations
**When to use:** Always - separates storage concerns from business logic
**Example:**
```python
# Source: Repository pattern standard practice
# https://www.cosmicpython.com/book/chapter_02_repository.html

from abc import ABC, abstractmethod
from typing import List, Optional

class ComprehensionRepository(ABC):
    """Abstract repository for comprehension persistence."""

    @abstractmethod
    def add(self, comprehension: Comprehension) -> None:
        """Persist a comprehension."""
        pass

    @abstractmethod
    def get(self, comprehension_id: str) -> Optional[Comprehension]:
        """Retrieve by ID."""
        pass

    @abstractmethod
    def find_by_domain(self, domain: str) -> List[Comprehension]:
        """Find all comprehensions in a domain."""
        pass

    @abstractmethod
    def find_by_topic(self, topic_query: str) -> List[Comprehension]:
        """Full-text search by topic."""
        pass

    @abstractmethod
    def find_by_confidence(
        self,
        min_confidence: ConfidenceLevel
    ) -> List[Comprehension]:
        """Find comprehensions at or above confidence level."""
        pass

    @abstractmethod
    def find_recent(self, limit: int = 10) -> List[Comprehension]:
        """Get most recently updated comprehensions."""
        pass


class SQLiteComprehensionRepository(ComprehensionRepository):
    """SQLite implementation of comprehension repository."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_schema()
```

### Pattern 2: SQLite with FTS5 for Topic Search
**What:** Full-text search on topic field for natural language queries
**When to use:** When retrieving comprehensions by topic similarity
**Example:**
```python
# Source: SQLite FTS5 documentation
# https://sqlite.org/fts5.html

import sqlite3

def create_fts_schema(conn: sqlite3.Connection):
    """Create comprehension table with FTS5 for topic search."""
    conn.executescript('''
        -- Main comprehension table
        CREATE TABLE IF NOT EXISTS comprehensions (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            topic TEXT NOT NULL,
            confidence TEXT NOT NULL,
            created TEXT NOT NULL,
            updated TEXT NOT NULL,
            version INTEGER NOT NULL,
            verified INTEGER NOT NULL,
            data JSON NOT NULL  -- Full Pydantic model as JSON
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_domain ON comprehensions(domain);
        CREATE INDEX IF NOT EXISTS idx_confidence ON comprehensions(confidence);
        CREATE INDEX IF NOT EXISTS idx_updated ON comprehensions(updated DESC);

        -- FTS5 virtual table for topic search
        CREATE VIRTUAL TABLE IF NOT EXISTS comprehensions_fts USING fts5(
            topic,
            content='comprehensions',
            content_rowid='rowid',
            tokenize='porter unicode61'
        );

        -- Triggers to keep FTS in sync
        CREATE TRIGGER IF NOT EXISTS comprehensions_ai AFTER INSERT ON comprehensions BEGIN
            INSERT INTO comprehensions_fts(rowid, topic)
            VALUES (new.rowid, new.topic);
        END;

        CREATE TRIGGER IF NOT EXISTS comprehensions_ad AFTER DELETE ON comprehensions BEGIN
            INSERT INTO comprehensions_fts(comprehensions_fts, rowid, topic)
            VALUES ('delete', old.rowid, old.topic);
        END;

        CREATE TRIGGER IF NOT EXISTS comprehensions_au AFTER UPDATE ON comprehensions BEGIN
            INSERT INTO comprehensions_fts(comprehensions_fts, rowid, topic)
            VALUES ('delete', old.rowid, old.topic);
            INSERT INTO comprehensions_fts(rowid, topic)
            VALUES (new.rowid, new.topic);
        END;
    ''')
```

### Pattern 3: Observation Reference Retention
**What:** Store observation IDs in comprehension, allow observation content pruning
**When to use:** Memory efficiency - observations are ephemeral, beliefs persist
**Example:**
```python
# Source: Project design principle
# "Storage is beliefs (posteriors), not evidence (observations)"

class ObservationIndex:
    """Lightweight index of observation references.

    Observation CONTENT can be pruned after incorporation.
    Observation REFERENCES remain in comprehension.observations list.
    This index tracks which observations still have content vs. pruned.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path

    def record_reference(
        self,
        observation_id: str,
        comprehension_id: str
    ) -> None:
        """Record that observation informed a comprehension."""
        # Store: observation_id -> list of comprehension_ids that reference it
        pass

    def mark_content_pruned(self, observation_id: str) -> None:
        """Mark observation content as deleted (reference remains)."""
        pass

    def get_referencing_comprehensions(
        self,
        observation_id: str
    ) -> List[str]:
        """Get comprehension IDs that reference this observation."""
        pass

    def can_prune(self, observation_id: str) -> bool:
        """Check if observation content can be safely pruned.

        Returns True if:
        1. Observation is incorporated (from lifecycle)
        2. All referencing comprehensions are verified
        """
        pass
```

### Pattern 4: Confidence Level Ordering
**What:** Map ConfidenceLevel enum to integers for SQL ordering/filtering
**When to use:** Queries like "confidence >= MEDIUM"
**Example:**
```python
# Source: Existing confidence.py enum + SQL query needs

CONFIDENCE_ORDER = {
    ConfidenceLevel.UNKNOWN: 0,
    ConfidenceLevel.LOW: 1,
    ConfidenceLevel.MEDIUM: 2,
    ConfidenceLevel.HIGH: 3,
}

def find_by_min_confidence(
    conn: sqlite3.Connection,
    min_level: ConfidenceLevel
) -> List[Comprehension]:
    """Find comprehensions at or above confidence level."""
    min_order = CONFIDENCE_ORDER[min_level]

    cursor = conn.execute('''
        SELECT data FROM comprehensions
        WHERE CASE confidence
            WHEN 'unknown' THEN 0
            WHEN 'low' THEN 1
            WHEN 'medium' THEN 2
            WHEN 'high' THEN 3
        END >= ?
        ORDER BY updated DESC
    ''', (min_order,))

    return [
        Comprehension.model_validate_json(row[0])
        for row in cursor.fetchall()
    ]
```

### Anti-Patterns to Avoid
- **Storing full observations alongside comprehensions:** Violates "beliefs not evidence" principle; causes storage to grow with evidence count
- **Vector search for structured queries:** Domain/confidence/recency are structured fields; use SQL indexes, not embeddings
- **Single table without indexes:** Will become slow; index domain, confidence, and updated timestamp
- **Eager loading all comprehensions:** Use pagination and filtering; avoid "load all" patterns
- **Synchronous file-per-comprehension:** I/O bound; use SQLite batch operations

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Full-text search | Custom tokenizer/indexer | SQLite FTS5 | Porter stemmer, BM25 ranking, triggers built in |
| JSON serialization | Custom encoder/decoder | Pydantic `model_dump_json()` / `model_validate_json()` | Handles datetime, enum, nested models |
| Migration tracking | Version field in code | Alembic or manual version table | Schema evolution needs rollback capability |
| Query building | f-strings with user input | Parameterized queries | SQL injection prevention |
| Connection pooling | Manual connection management | sqlite3 with context manager | RAII pattern handles cleanup |

**Key insight:** SQLite FTS5 provides battle-tested full-text search. The project's scale (hundreds to low thousands of comprehensions) doesn't justify custom search infrastructure or external vector databases.

## Common Pitfalls

### Pitfall 1: Treating Observations as Persistent
**What goes wrong:** Storing full observation content permanently causes storage to grow with evidence count, not understanding
**Why it happens:** Intuition that "more data is better"; fear of data loss
**How to avoid:** Enforce the design: observations are ephemeral, comprehensions persist. Observation IDs are retained as references, content is prunable.
**Warning signs:** Observation table growing faster than comprehension table; storage size correlating with activity, not comprehension count

### Pitfall 2: Full-Text Search on Wrong Fields
**What goes wrong:** Using FTS5 on `posterior.statement` instead of `topic` returns noisy results
**Why it happens:** Statement is longer, seems like better search target
**How to avoid:** FTS5 on topic (what it's about), SQL filter on domain (category). Statement contains reasoning, not retrieval keys.
**Warning signs:** Search results that are topically similar but in wrong domain

### Pitfall 3: Confidence as String Comparison
**What goes wrong:** SQL query `WHERE confidence >= 'medium'` gives wrong results (alphabetical, not ordinal)
**Why it happens:** ConfidenceLevel.value is string 'high', 'medium', etc.
**How to avoid:** Use CASE expression or store numeric confidence_order column
**Warning signs:** HIGH confidence excluded from "confidence >= MEDIUM" queries

### Pitfall 4: Ignoring Recency for Tie-Breaking
**What goes wrong:** Two comprehensions on same topic both returned; no way to prefer more recent
**Why it happens:** Only filtering by domain/topic, not ordering
**How to avoid:** Always ORDER BY updated DESC as final sort
**Warning signs:** Old, possibly superseded comprehensions returned before newer ones

### Pitfall 5: N+1 Query Pattern
**What goes wrong:** Loading comprehensions one-by-one in a loop
**Why it happens:** Natural to `get(id)` for each item in a list
**How to avoid:** Batch queries: `WHERE id IN (?, ?, ?)` or use `find_by_*` methods that return lists
**Warning signs:** Query count scaling linearly with comprehension count

### Pitfall 6: Missing Version Conflicts
**What goes wrong:** Two processes update same comprehension; last write wins, first update lost
**Why it happens:** No optimistic concurrency control
**How to avoid:** Check version on update: `WHERE id = ? AND version = ?`; fail if 0 rows updated
**Warning signs:** Lost updates when concurrent agents operate on same comprehension

## Code Examples

Verified patterns from official sources:

### SQLite Connection with JSON Support
```python
# Source: Python sqlite3 docs
# https://docs.python.org/3/library/sqlite3.html

import sqlite3
import json
from pathlib import Path

def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Create SQLite connection with JSON and datetime support."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name

    # Enable JSON functions (built into SQLite 3.38+)
    # For older: conn.execute("SELECT json('[]')")  # Test availability

    return conn
```

### Pydantic Model Persistence
```python
# Source: Pydantic v2 serialization docs
# https://docs.pydantic.dev/latest/concepts/serialization/

from comprehension.schema import Comprehension

def save_comprehension(
    conn: sqlite3.Connection,
    comp: Comprehension
) -> None:
    """Persist a comprehension to SQLite."""
    conn.execute('''
        INSERT OR REPLACE INTO comprehensions
        (id, domain, topic, confidence, created, updated, version, verified, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        comp.id,
        comp.domain,
        comp.topic,
        comp.posterior.confidence.value,  # Store enum value
        comp.created.isoformat(),
        comp.updated.isoformat(),
        comp.version,
        1 if comp.verified else 0,
        comp.model_dump_json(),  # Full model as JSON
    ))
    conn.commit()


def load_comprehension(
    conn: sqlite3.Connection,
    comprehension_id: str
) -> Comprehension | None:
    """Load a comprehension from SQLite."""
    cursor = conn.execute(
        'SELECT data FROM comprehensions WHERE id = ?',
        (comprehension_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Comprehension.model_validate_json(row['data'])
```

### FTS5 Topic Search with BM25 Ranking
```python
# Source: SQLite FTS5 docs
# https://sqlite.org/fts5.html

def search_by_topic(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 10
) -> list[Comprehension]:
    """Full-text search on topic field with BM25 ranking."""
    cursor = conn.execute('''
        SELECT c.data, bm25(comprehensions_fts) as rank
        FROM comprehensions c
        JOIN comprehensions_fts f ON c.rowid = f.rowid
        WHERE comprehensions_fts MATCH ?
        ORDER BY rank  -- Lower BM25 score = more relevant
        LIMIT ?
    ''', (query, limit))

    return [
        Comprehension.model_validate_json(row['data'])
        for row in cursor.fetchall()
    ]
```

### Multi-Dimensional Query
```python
# Retrieve comprehensions by domain + confidence + recency

def find_relevant(
    conn: sqlite3.Connection,
    domain: str | None = None,
    min_confidence: ConfidenceLevel | None = None,
    topic_query: str | None = None,
    limit: int = 20
) -> list[Comprehension]:
    """Find comprehensions matching multiple criteria."""
    conditions = []
    params = []

    # Base query
    if topic_query:
        # Use FTS5 join for topic search
        base = '''
            SELECT c.data FROM comprehensions c
            JOIN comprehensions_fts f ON c.rowid = f.rowid
            WHERE comprehensions_fts MATCH ?
        '''
        params.append(topic_query)
    else:
        base = 'SELECT data FROM comprehensions WHERE 1=1'

    # Domain filter
    if domain:
        conditions.append('domain = ?')
        params.append(domain)

    # Confidence filter
    if min_confidence:
        min_order = CONFIDENCE_ORDER[min_confidence]
        conditions.append('''
            CASE confidence
                WHEN 'unknown' THEN 0
                WHEN 'low' THEN 1
                WHEN 'medium' THEN 2
                WHEN 'high' THEN 3
            END >= ?
        ''')
        params.append(min_order)

    # Build final query
    query = base
    if conditions:
        query += ' AND ' + ' AND '.join(conditions)
    query += ' ORDER BY updated DESC LIMIT ?'
    params.append(limit)

    cursor = conn.execute(query, params)
    return [
        Comprehension.model_validate_json(row[0])
        for row in cursor.fetchall()
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Full observation storage | Belief compression, observation pruning | 2025-2026 | 89-95% storage reduction per Mem0 research |
| Vector-only retrieval | Hybrid FTS5 + vector | 2024-2025 | Better relevance for keyword + semantic queries |
| Global confidence levels | Structured confidence with provenance | 2025 | Enables confidence-based retrieval |
| Unstructured text memories | State-based memory with belief updates | 2025-2026 | Prevents fact accumulation, supports updates |

**Deprecated/outdated:**
- **sqlite-vss:** Deprecated, replaced by sqlite-vec for vector search
- **Pydantic v1 `.parse_obj()`:** Use `.model_validate()` in Pydantic v2
- **RAG-style "load all context":** Memory control paradigm prefers compact, curated beliefs

## Open Questions

1. **Observation content storage location**
   - What we know: Observation IDs are retained in comprehension.observations list; content can be pruned
   - What's unclear: Should observations be stored in same DB or separate file system? How long to retain before pruning?
   - Recommendation: Store in same SQLite DB initially; add retention policy parameter (e.g., prune_after_days=30)

2. **Comprehension versioning strategy**
   - What we know: Comprehension has version field; updates increment it
   - What's unclear: Should old versions be retained for rollback, or overwritten?
   - Recommendation: Start with overwrite (INSERT OR REPLACE); add version history table if rollback needed

3. **Concurrent access from multiple agents**
   - What we know: SQLite handles concurrent reads well; writes are serialized
   - What's unclear: Will multiple agents update same comprehension simultaneously?
   - Recommendation: Implement optimistic locking via version check; document that concurrent writes to same comprehension may fail

4. **Semantic retrieval for topic search**
   - What we know: FTS5 provides keyword search; vector search enables semantic similarity
   - What's unclear: Will keyword search be sufficient for Phase 3 requirements?
   - Recommendation: Start with FTS5 only; add sqlite-vec or ChromaDB if keyword search proves insufficient

## Sources

### Primary (HIGH confidence)
- [SQLite FTS5 Extension](https://sqlite.org/fts5.html) - Official FTS5 documentation, tokenizers, BM25 ranking
- [Pydantic Serialization Docs](https://docs.pydantic.dev/latest/concepts/serialization/) - model_dump, model_dump_json, model_validate
- [Python sqlite3 Module](https://docs.python.org/3/library/sqlite3.html) - Connection management, row_factory, parameterized queries
- [Repository Pattern - Cosmic Python](https://www.cosmicpython.com/book/chapter_02_repository.html) - Repository abstraction pattern

### Secondary (MEDIUM confidence)
- [Hybrid SQLite FTS5 + Vector Search](https://alexgarcia.xyz/blog/2024/sqlite-vec-hybrid-search/index.html) - Alex Garcia's sqlite-vec hybrid search guide
- [sqlite-vec GitHub](https://github.com/asg017/sqlite-vec) - Vector search extension documentation
- [Memory for AI Agents - The New Stack](https://thenewstack.io/memory-for-ai-agents-a-new-paradigm-of-context-engineering/) - State-based vs retrieval-based memory
- [OpenAI Agents SDK Context Personalization](https://cookbook.openai.com/examples/agents_sdk/context_personalization) - Belief update patterns, state management
- [pydantic-sqlite](https://github.com/Phil997/pydantic-sqlite) - Pydantic + SQLite integration patterns

### Tertiary (LOW confidence - needs validation)
- [Mem0 Paper](https://arxiv.org/pdf/2504.19413) - 89-95% compression rates claim (research paper, not production validated)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - SQLite and Pydantic are proven, in-use technologies
- Architecture: HIGH - Repository pattern is well-established; SQLite FTS5 is documented
- Pitfalls: MEDIUM - Some pitfalls are project-specific (belief vs evidence); verified against existing Phase 1-2 design

**Research date:** 2026-02-13
**Valid until:** 2026-03-15 (30 days - stable domain)
