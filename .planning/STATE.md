# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-13)

**Core value:** Understanding is computation.
**Current focus:** Phase 4 - Convergence Detection

## Current Position

Phase: 4 of 7 (Convergence Detection)
Plan: 1 of 3 in current phase (04-01 complete)
Status: In progress
Last activity: 2026-02-13 — Completed 04-01 Embeddings & Vector Store

Progress: [████░░░░░░] 43% (3/7 phases)

## Architecture Reference

See: .planning/ARCHITECTURE_SKETCH.md

```
Experience → Observation → Comprehension → Meta-comprehension → The Web
                 ↑              ↑                  ↑
            selective      Bayesian          convergence
            recording       update           detection
```

## Phase Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | Cognitive Primitives | ✓ Complete |
| 2 | Bayesian Update | ✓ Complete |
| 3 | Belief Store | ✓ Complete |
| 4 | Convergence Detection | ◆ Current |
| 5 | Meta-Comprehension | ○ Pending |
| 6 | The Web | ○ Pending |
| 7 | API Harness | ○ Pending |

## Performance Metrics

**Velocity:**
- Total plans completed: 3 (Phase 1)
- Average duration: -
- Total execution time: ~1 session

**By Phase:**

| Phase | Plans | Status |
|-------|-------|--------|
| 1 | 3/3 | ✓ Complete |
| 2 | 3/3 | ✓ Complete |
| 3 | 3/3 | ✓ Complete |

**Plan 02-01:** 2min - Confidence transition state machine
**Plan 02-02:** 2min - Bayesian update function
**Plan 02-03:** 2min - Observation lifecycle management
**Plan 03-01:** 2min - SQLite Repository with CRUD operations
**Plan 03-02:** 4min - Multi-dimensional retrieval with FTS5
**Plan 03-03:** 3min - BeliefStore facade and ObservationIndex
**Plan 04-01:** 3min - Embeddings & Vector Store (sentence-transformers, sqlite-vec)

## Accumulated Context

### Key Insights

1. **The posterior IS compression** — No separate compression step; belief update compresses evidence into understanding

2. **Rising tide emergence** — Don't search for patterns; let them become obvious through accumulation (Grothendieck)

3. **Patterns between patterns** — The best abstraction notices analogies between theories, not just theorems (Banach)

4. **Memory efficiency** — Store beliefs, not evidence; observations are ephemeral, comprehensions persist

### Decisions

| Decision | Rationale | Phase |
|----------|-----------|-------|
| Language confidence, not numeric | LLMs work in language; false precision avoided | 1 |
| Posterior as compression | Bayesian update IS the compression operation | 2 |
| Structural similarity for convergence | Same shape, not same keywords | 4 |
| Rising tide over forced abstraction | Emergence, not construction | 4-5 |
| Deterministic state machine for transitions | No LLM judgment for confidence changes | 2 |
| Contradicting on UNKNOWN -> LOW | Learning something from contradiction | 2 |
| INCORPORATED == COLLECTIBLE | Retention policies deferred to future | 2 |
| Lifecycle not thread-safe | Callers handle synchronization | 2 |
| Idempotency via observation ID | Simple check before processing | 2 |
| Contradicting requires new_statement | Enforced via ValueError | 2 |
| JSON blob with indexed fields | Full model as JSON, extracted fields for queries | 3 |
| Connection-per-operation | Thread safety via fresh connections | 3 |
| INSERT OR REPLACE for upsert | Duplicate save updates existing record | 3 |
| FTS5 with Porter stemmer | Word stemming for natural language search | 3 |
| BM25 ranking for topic search | Standard IR ranking algorithm | 3 |
| Ordinal confidence mapping | UNKNOWN=0, LOW=1, MEDIUM=2, HIGH=3 | 3 |
| Trigger-based FTS sync | Automatic consistency without app coordination | 3 |
| ObservationIndex shares database | Same SQLite file as repository, avoids complexity | 3 |
| Composite PK for observation refs | (observation_id, comprehension_id) for many-to-many | 3 |
| BeliefStore auto-manages index | save() records refs, delete() cleans them up | 3 |
| Pruning is marking not deleting | observation_pruned table tracks deleted content | 3 |
| API harness over agent tools | Understanding automatic, not opt-in; wraps all model calls | 7 |
| all-MiniLM-L6-v2 for embeddings | Balance of quality (384 dims) and speed (22MB) | 4 |
| Prior + posterior embedding | Captures belief transformation shape, not just topic | 4 |
| sqlite-vec k=? syntax | KNN queries require k in WHERE clause, not LIMIT | 4 |
| Hash-based rowid mapping | Stable positive int32 keys via hash & 0x7FFFFFFF | 4 |

### Open Questions

1. How to detect structural similarity across domains? (Phase 4)
2. What are the emergence thresholds for crystallization? (Phase 5)
3. Observation retention policy before GC? (Phase 2/3)
4. SDK wrapper vs proxy server for harness? (Phase 7)
5. How to extract domain/topic signals from prompts? (Phase 7)
6. How much belief context to inject without blowing up token usage? (Phase 7)
7. Async vs sync observation extraction and update? (Phase 7)

## Session Continuity

Last session: 2026-02-13
Stopped at: Completed 04-01-PLAN.md (Embeddings & Vector Store)
Next: Execute 04-02-PLAN.md (Similarity Detection)

---
*Next: /gsd:execute-phase 04-02*
