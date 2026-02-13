# Phase 4: Convergence Detection - Research

**Researched:** 2026-02-13
**Domain:** Structural similarity detection, embedding-based search, density tracking
**Confidence:** MEDIUM (novel domain requiring synthesis of established techniques)

## Summary

Phase 4 implements the "reminds me of" operation: when a new comprehension is created, the system queries for structurally similar existing comprehensions across domains. The key insight from the architecture is that **similarity must be structural (same shape), not keyword-based**. This prevents false matches on terminology while enabling pattern recognition across different domains.

The recommended approach combines **semantic embeddings** (sentence-transformers) with **vector similarity search** (sqlite-vec) to detect structural similarity. The prior/posterior belief statements are embedded as vectors, and similarity is computed via cosine distance. Domain diversity is tracked separately to identify when the same pattern appears across multiple domains (rising tide).

**Primary recommendation:** Embed comprehension belief statements using all-MiniLM-L6-v2 (384 dimensions), store vectors in sqlite-vec virtual tables, and perform KNN queries on new comprehension creation. Track domain diversity separately in accumulation metadata.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sentence-transformers | 3.x | Generate semantic embeddings | 15K+ pretrained models, state-of-the-art MTEB scores, simple API |
| sqlite-vec | 0.1.x | Vector similarity search in SQLite | Pure C, no dependencies, integrates with existing SQLite, brute-force is fast enough for <100K vectors |
| all-MiniLM-L6-v2 | - | Embedding model | 384 dimensions, 22MB, fast, 156M+ monthly downloads, good quality/speed tradeoff |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| numpy | 1.x/2.x | Vector operations | Efficient array handling for embeddings |
| struct | stdlib | Binary serialization | Converting float lists to SQLite BLOB format |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sqlite-vec | FAISS | FAISS is faster for millions of vectors but adds complexity; sqlite-vec is simpler for <100K |
| all-MiniLM-L6-v2 | all-mpnet-base-v2 | mpnet is more accurate (87-88% vs 84-85% STS-B) but 5x larger (110M vs 22M params) |
| Brute-force KNN | HNSW index | HNSW supports incremental updates but sqlite-vec brute-force is fast enough for our scale |
| Embeddings | LLM-as-judge | LLM provides richer comparison but costs tokens; embeddings are cheap and fast |

**Installation:**
```bash
pip install sentence-transformers sqlite-vec numpy
```

## Architecture Patterns

### Recommended Project Structure
```
src/comprehension/
├── convergence/           # NEW: Phase 4 module
│   ├── __init__.py
│   ├── embedder.py        # SentenceTransformer wrapper
│   ├── similarity.py      # "reminds me of" query operation
│   ├── accumulator.py     # Density tracking across domains
│   └── vector_store.py    # sqlite-vec integration
├── schema/                # Existing
├── update/                # Existing
└── store/                 # Existing (BeliefStore)
```

### Pattern 1: Embedding at Write Time

**What:** Generate and store embeddings when a comprehension is saved, not at query time.
**When to use:** Always - embeddings are expensive to compute repeatedly.
**Example:**
```python
# Source: sentence-transformers official usage
from sentence_transformers import SentenceTransformer

class ComprehensionEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformer(model_name)

    def embed(self, comprehension: Comprehension) -> np.ndarray:
        """Embed the structural content of a comprehension."""
        # Combine prior and posterior statements for embedding
        # This captures the "shape" of the belief transformation
        text = f"{comprehension.prior.statement} {comprehension.posterior.statement}"
        return self._model.encode(text, normalize_embeddings=True)
```

### Pattern 2: Similarity Query with Domain Exclusion

**What:** When asking "what reminds me of this?", exclude same-domain matches to find cross-domain patterns.
**When to use:** Core operation for convergence detection.
**Example:**
```python
# Source: sqlite-vec documentation
def find_similar(
    self,
    embedding: bytes,
    exclude_domain: str,
    limit: int = 5,
    min_similarity: float = 0.7
) -> List[SimilarityMatch]:
    """Find comprehensions with similar structure from OTHER domains."""
    rows = self._conn.execute("""
        SELECT c.id, c.domain, v.distance
        FROM comprehension_vectors v
        JOIN comprehensions c ON c.id = v.comprehension_id
        WHERE v.embedding MATCH ?
          AND c.domain != ?
          AND v.distance < ?
        ORDER BY v.distance
        LIMIT ?
    """, [embedding, exclude_domain, 1 - min_similarity, limit]).fetchall()
    return [SimilarityMatch(id=r[0], domain=r[1], similarity=1-r[2]) for r in rows]
```

### Pattern 3: Accumulation Tracking

**What:** Track where comprehension density is building to enable "rising tide" detection.
**When to use:** For identifying candidate patterns before meta-comprehension crystallization (Phase 5).
**Example:**
```python
class AccumulationTracker:
    """Track where structural similarity is accumulating across domains."""

    def record_similarity(
        self,
        source_id: str,
        target_id: str,
        similarity: float,
        source_domain: str,
        target_domain: str
    ) -> None:
        """Record that two comprehensions are structurally similar."""
        # Store in similarity_edges table
        # This builds a graph of structural relationships
        pass

    def get_accumulation_hotspots(
        self,
        min_domains: int = 2,
        min_connections: int = 3
    ) -> List[AccumulationHotspot]:
        """Find clusters where similar structures are accumulating."""
        # Query for comprehensions with connections across multiple domains
        pass
```

### Pattern 4: sqlite-vec Virtual Table Integration

**What:** Store vectors in sqlite-vec virtual tables alongside existing comprehensions table.
**When to use:** For efficient KNN queries without external dependencies.
**Example:**
```python
# Source: sqlite-vec simple-python/demo.py
import sqlite3
import sqlite_vec
import struct

def serialize_f32(vector: list) -> bytes:
    """Serialize float list to compact binary format."""
    return struct.pack("%sf" % len(vector), *vector)

# Setup
db = sqlite3.connect("beliefs.db")
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

# Create vector table (384 dimensions for all-MiniLM-L6-v2)
db.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS comprehension_vectors
    USING vec0(
        comprehension_id TEXT PRIMARY KEY,
        embedding float[384]
    )
""")

# Insert
db.execute(
    "INSERT INTO comprehension_vectors(comprehension_id, embedding) VALUES (?, ?)",
    [comp_id, serialize_f32(embedding.tolist())]
)

# KNN query
rows = db.execute("""
    SELECT comprehension_id, distance
    FROM comprehension_vectors
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 5
""", [serialize_f32(query_embedding.tolist())]).fetchall()
```

### Anti-Patterns to Avoid

- **Keyword-based similarity:** Using FTS5 text matching for convergence detection misses structural patterns and creates false positives on terminology. Use embeddings for structure, FTS5 for topic search (already implemented in Phase 3).

- **Same-domain matching:** Including same-domain comprehensions in similarity results creates noise. The goal is to find patterns ACROSS domains.

- **Query-time embedding:** Computing embeddings on every similarity query is expensive. Embed at write time.

- **Eager meta-comprehension:** Don't create meta-comprehensions in Phase 4. Just detect and track similarity. Crystallization happens in Phase 5.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Semantic embeddings | Custom word2vec/TF-IDF | sentence-transformers | State-of-the-art quality, pretrained on 1B+ pairs |
| Vector similarity search | Numpy dot products in Python | sqlite-vec | SIMD-optimized C, integrates with existing SQLite |
| Binary serialization | Custom JSON/pickle | struct.pack | Standard format, matches sqlite-vec expectations |
| Model loading | Manual transformers setup | SentenceTransformer class | Handles pooling, normalization automatically |

**Key insight:** The embedding and similarity search problem space is mature. The complexity in this phase is in the DESIGN of what to embed and how to use similarity results, not the mechanics.

## Common Pitfalls

### Pitfall 1: Similarity Threshold Selection

**What goes wrong:** Setting threshold too high misses valid patterns; too low creates noise.
**Why it happens:** Cosine similarity distributions vary by model and use case.
**How to avoid:** Start with 0.7-0.75 threshold, log all matches with scores, tune based on observed quality. Newer models (text-embedding-3-*) have different distributions than older models.
**Warning signs:** Too few matches (>0.85) or too many irrelevant matches (<0.6).

### Pitfall 2: Embedding What?

**What goes wrong:** Embedding wrong content (e.g., just topic) fails to capture structural similarity.
**Why it happens:** "Structure" is abstract; easy to embed surface features instead.
**How to avoid:** Embed the belief transformation: prior.statement + posterior.statement. This captures the "shape" of the insight, not just the subject matter.
**Warning signs:** High similarity between comprehensions that "feel" different structurally.

### Pitfall 3: Domain Leakage

**What goes wrong:** Same-domain matches dominate results because they share vocabulary.
**Why it happens:** Comprehensions in the same domain naturally use similar terminology.
**How to avoid:** Always exclude the source comprehension's domain from similarity queries. Cross-domain similarity is the signal.
**Warning signs:** All top matches come from the same domain.

### Pitfall 4: Model Loading Overhead

**What goes wrong:** Loading sentence-transformer model on every operation causes latency.
**Why it happens:** Models take 1-3 seconds to initialize.
**How to avoid:** Initialize model once and reuse. Cache in module-level singleton or pass as dependency.
**Warning signs:** Slow save operations, memory growth.

### Pitfall 5: sqlite-vec Extension Loading on macOS

**What goes wrong:** Extension fails to load with default macOS Python.
**Why it happens:** macOS system Python disables loadable extensions.
**How to avoid:** Use Homebrew Python (`brew install python`) or pyenv-installed Python. Test extension loading in CI.
**Warning signs:** "Error loading extension" or "enable_load_extension" errors.

## Code Examples

### Complete "Reminds Me Of" Query

```python
# Source: Synthesis of sentence-transformers and sqlite-vec docs
from dataclasses import dataclass
from typing import List, Optional
import numpy as np
import sqlite3
import sqlite_vec
import struct

from sentence_transformers import SentenceTransformer
from comprehension.schema import Comprehension

@dataclass
class SimilarityMatch:
    comprehension_id: str
    domain: str
    similarity: float  # 0-1, higher is more similar

class ConvergenceDetector:
    """Detects structural similarity across comprehensions."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._model = SentenceTransformer("all-MiniLM-L6-v2")
        self._init_vector_table()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return conn

    def _init_vector_table(self) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS comprehension_vectors
                USING vec0(embedding float[384])
            """)
            conn.commit()
        finally:
            conn.close()

    def _embed(self, comprehension: Comprehension) -> np.ndarray:
        """Generate embedding from belief transformation structure."""
        text = f"{comprehension.prior.statement} {comprehension.posterior.statement}"
        return self._model.encode(text, normalize_embeddings=True)

    @staticmethod
    def _serialize(vector: np.ndarray) -> bytes:
        return struct.pack("%sf" % len(vector), *vector.tolist())

    def index_comprehension(self, comprehension: Comprehension) -> None:
        """Add comprehension embedding to vector index."""
        embedding = self._embed(comprehension)
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO comprehension_vectors(rowid, embedding) VALUES (?, ?)",
                [hash(comprehension.id) & 0x7FFFFFFF, self._serialize(embedding)]
            )
            # Store mapping separately (comprehension_vectors uses rowid)
            conn.execute(
                "INSERT OR REPLACE INTO vector_id_map(rowid, comprehension_id) VALUES (?, ?)",
                [hash(comprehension.id) & 0x7FFFFFFF, comprehension.id]
            )
            conn.commit()
        finally:
            conn.close()

    def reminds_me_of(
        self,
        comprehension: Comprehension,
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[SimilarityMatch]:
        """Find structurally similar comprehensions from OTHER domains."""
        embedding = self._embed(comprehension)
        max_distance = 1 - min_similarity  # cosine distance = 1 - similarity

        conn = self._connect()
        try:
            rows = conn.execute("""
                SELECT
                    m.comprehension_id,
                    c.domain,
                    v.distance
                FROM comprehension_vectors v
                JOIN vector_id_map m ON m.rowid = v.rowid
                JOIN comprehensions c ON c.id = m.comprehension_id
                WHERE v.embedding MATCH ?
                  AND c.domain != ?
                  AND v.distance < ?
                ORDER BY v.distance
                LIMIT ?
            """, [
                self._serialize(embedding),
                comprehension.domain,
                max_distance,
                limit
            ]).fetchall()

            return [
                SimilarityMatch(
                    comprehension_id=row[0],
                    domain=row[1],
                    similarity=1 - row[2]  # Convert distance back to similarity
                )
                for row in rows
            ]
        finally:
            conn.close()
```

### Accumulation Tracking Schema

```sql
-- Track similarity relationships for rising tide detection
CREATE TABLE IF NOT EXISTS similarity_edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    similarity REAL NOT NULL,
    source_domain TEXT NOT NULL,
    target_domain TEXT NOT NULL,
    created TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id)
);

-- Index for finding clusters
CREATE INDEX IF NOT EXISTS idx_similarity_target
ON similarity_edges(target_id, similarity);

-- Query: Find comprehensions with connections across multiple domains
SELECT
    target_id,
    COUNT(DISTINCT source_domain) as domain_count,
    COUNT(*) as connection_count,
    AVG(similarity) as avg_similarity
FROM similarity_edges
GROUP BY target_id
HAVING domain_count >= 2 AND connection_count >= 3
ORDER BY domain_count DESC, avg_similarity DESC;
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| TF-IDF + cosine | Transformer embeddings | 2019 (BERT) | Much better semantic capture |
| Word2Vec averaging | Sentence transformers | 2019 (SBERT) | Purpose-built sentence embeddings |
| External vector DB (Pinecone, etc.) | sqlite-vec | 2024 (v0.1.0) | Local-first, no infrastructure |
| FAISS for all vector search | sqlite-vec for <100K | 2024 | Simpler stack for moderate scale |

**Deprecated/outdated:**
- sqlite-vss: Superseded by sqlite-vec (same author, simpler, no dependencies)
- text-embedding-ada-002 thresholds: Newer OpenAI models have different similarity distributions

## Open Questions

1. **Embedding content composition**
   - What we know: Prior + posterior statements capture belief transformation shape
   - What's unclear: Should we include topic? Confidence level? Observation count?
   - Recommendation: Start with prior + posterior only; add fields if similarity quality is poor

2. **Similarity threshold tuning**
   - What we know: 0.7-0.8 is typical starting range for semantic similarity
   - What's unclear: Optimal threshold for this specific use case
   - Recommendation: Start at 0.75, log all matches, tune based on observed quality

3. **When to run convergence detection**
   - What we know: Running on every save is cleanest but has cost
   - What's unclear: Performance impact at scale
   - Recommendation: Run synchronously on save initially; batch/async if performance requires

4. **Integration with BeliefStore**
   - What we know: ConvergenceDetector needs to coordinate with existing BeliefStore
   - What's unclear: Should it wrap BeliefStore or be called separately?
   - Recommendation: Compose via a higher-level service that calls both, keeping them decoupled

## Sources

### Primary (HIGH confidence)
- [sentence-transformers PyPI](https://pypi.org/project/sentence-transformers/) - Installation, API
- [Sentence Transformers Semantic Textual Similarity](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html) - Official usage guide
- [sqlite-vec Python documentation](https://alexgarcia.xyz/sqlite-vec/python.html) - Installation, API
- [sqlite-vec GitHub demo](https://github.com/asg017/sqlite-vec/blob/main/examples/simple-python/demo.py) - Complete working example
- [all-MiniLM-L6-v2 Hugging Face](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) - Model specifications

### Secondary (MEDIUM confidence)
- [HDBSCAN prediction tutorial](https://hdbscan.readthedocs.io/en/latest/prediction_tutorial.html) - Incremental clustering approach
- [Milvus incremental updates](https://milvus.io/ai-quick-reference/how-do-you-handle-incremental-updates-in-a-vector-database) - Vector DB update patterns
- [OpenAI similarity thresholds discussion](https://community.openai.com/t/rule-of-thumb-cosine-similarity-thresholds/693670) - Threshold selection guidance
- [Embeddings similarity threshold analysis](https://www.s-anand.net/blog/embeddings-similarity-threshold/) - Practical threshold tuning

### Tertiary (LOW confidence)
- WebSearch results on structural vs semantic similarity - Conceptual framing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Well-established libraries with extensive documentation
- Architecture patterns: MEDIUM - Synthesized from library docs and domain knowledge
- Pitfalls: MEDIUM - Combination of documented issues and inferred challenges
- Code examples: MEDIUM - Working syntax verified but not integration-tested

**Research date:** 2026-02-13
**Valid until:** 2026-03-15 (sqlite-vec and sentence-transformers are stable; patterns are durable)
