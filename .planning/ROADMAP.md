# Roadmap: Comprehension-as-Code

## Overview

A computational theory of understanding. The roadmap follows the cognitive architecture:
primitives → operations → storage → emergence → harness.

Phases 1-3 built the core engine (primitives, Bayesian update, persistence). Remaining phases build emergence (convergence, meta-comprehension, web) and the API harness that makes understanding automatic.

**Architectural pivot (2026-02-13):** Instead of agents explicitly calling tools to query/update beliefs, an API harness intercepts all model interactions and handles understanding automatically. Every interaction builds understanding without explicit action.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Cognitive Primitives** - Define schemas for Observation, Comprehension, Confidence
- [x] **Phase 2: Bayesian Update** - The core operation: observation + prior → posterior
- [x] **Phase 3: Belief Store** - Persistence with memory efficiency (beliefs, not evidence)
- [ ] **Phase 4: Convergence Detection** - Notice "same shape" across domains (rising tide)
- [ ] **Phase 5: Meta-Comprehension** - Emergence conditions and crystallization
- [ ] **Phase 6: The Web** - Implicit connections, traversal, bootstrap
- [ ] **Phase 7: API Harness** - Middleware that wraps model calls with automatic understanding

## Phase Details

### Phase 1: Cognitive Primitives ✓
**Goal**: Schemas exist that define the primitive types for understanding
**Depends on**: Nothing (first phase)
**Requirements**: Observation schema, Comprehension schema, ConfidenceLevel enum
**Status**: COMPLETE
**Success Criteria** (what must be TRUE):
  1. ✓ Observation model captures ephemeral events
  2. ✓ Comprehension model has Bayesian structure (prior/posterior)
  3. ✓ Confidence levels defined in natural language
  4. ✓ Sample documents validate against schemas

### Phase 2: Bayesian Update ✓
**Goal**: The core operation works: observations update beliefs, and the posterior IS the compression
**Depends on**: Phase 1
**Requirements**: Update operation, provenance tracking, observation lifecycle
**Status**: COMPLETE
**Success Criteria** (what must be TRUE):
  1. ✓ Given observation + existing comprehension → new posterior computed
  2. ✓ Confidence level updates based on evidence (confirming → higher, contradicting → lower)
  3. ✓ Provenance tracks which observations informed belief (references, not copies)
  4. ✓ Observations can be garbage collected after informing comprehension
  5. ✓ The update operation IS compression (no separate compress step)

**Plans:** 3 plans

Plans:
- [x] 02-01-PLAN.md - Confidence transition state machine (TDD, Wave 1)
- [x] 02-02-PLAN.md - Core Bayesian update operation (TDD, Wave 2)
- [x] 02-03-PLAN.md - Observation lifecycle management (Wave 1)

### Phase 3: Belief Store ✓
**Goal**: Comprehensions persist with memory efficiency; retrieval is by relevance, not "load all"
**Depends on**: Phase 2
**Requirements**: Persistence layer, retrieval, memory model
**Status**: COMPLETE
**Success Criteria** (what must be TRUE):
  1. ✓ Comprehensions persist across sessions
  2. ✓ Retrieval by domain, topic, confidence, recency
  3. ✓ Storage is beliefs (posteriors), not evidence (observations)
  4. ✓ Observation references are maintained; observation content can be pruned
  5. ✓ Storage grows with understanding, not with evidence count

**Plans:** 3 plans

Plans:
- [x] 03-01-PLAN.md - SQLite repository + schema (TDD, Wave 1)
- [x] 03-02-PLAN.md - Multi-dimensional retrieval + FTS5 (TDD, Wave 2)
- [x] 03-03-PLAN.md - BeliefStore facade + ObservationIndex (Wave 3)

### Phase 4: Convergence Detection
**Goal**: System notices when the same structure appears across domains (rising tide)
**Depends on**: Phase 3
**Requirements**: Structural similarity, "reminds me of" operation, accumulation tracking
**Success Criteria** (what must be TRUE):
  1. Each new comprehension can query "what does this remind me of?"
  2. Similarity is structural (same shape), not keyword-based
  3. System tracks where comprehension density is building
  4. Candidate patterns emerge from repeated structure (not explicit search)
  5. Rising tide: accumulation creates conditions for pattern recognition

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

### Phase 5: Meta-Comprehension
**Goal**: Patterns crystallize into named meta-comprehensions when confidence is high
**Depends on**: Phase 4
**Requirements**: Emergence conditions (Bayesian), crystallization, pattern-of-patterns
**Success Criteria** (what must be TRUE):
  1. Emergence conditions defined: min instances, domain diversity, confidence threshold
  2. Meta-confidence computed from instance confidences
  3. Crystallization: when threshold met, pattern becomes named meta-comprehension
  4. Meta-comprehension references instances but doesn't duplicate them
  5. New comprehensions can be recognized as "another instance of pattern X"

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: The Web
**Goal**: Understanding forms an implicit web of connected patterns; agents can traverse and bootstrap
**Depends on**: Phase 5
**Requirements**: Implicit connections, navigation, bootstrap protocol
**Success Criteria** (what must be TRUE):
  1. Connections exist through structural similarity (no explicit edge creation)
  2. Traversal: from one comprehension, find related comprehensions
  3. Navigation: from meta-comprehension, access instances
  4. Bootstrap: new agent loads relevant meta-comprehensions + domain comprehensions
  5. Understanding is the web, not a list of documents

Plans:
- [ ] 06-01: TBD
- [ ] 06-02: TBD

### Phase 7: API Harness
**Goal**: Middleware wraps all model interactions; understanding is automatic, not opt-in
**Depends on**: Phase 6
**Requirements**: Request interception, belief enrichment, observation extraction, update triggers
**Success Criteria** (what must be TRUE):
  1. Harness intercepts all model API requests transparently
  2. Harness extracts domain/topic signals and queries relevant comprehensions
  3. Harness enriches prompts with belief context (automatic, not tool-based)
  4. Harness extracts observations from model interactions
  5. Harness triggers Bayesian updates and convergence detection
  6. Bootstrap: new sessions start with accumulated understanding
  7. Full loop: interaction → observation → comprehension → meta-comprehension → enriched interaction
  8. Client-transparent: response unchanged, understanding accumulates invisibly

Plans:
- [ ] 07-01: TBD
- [ ] 07-02: TBD
- [ ] 07-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Cognitive Primitives | 3/3 | ✓ Complete | 2026-02-13 |
| 2. Bayesian Update | 3/3 | ✓ Complete | 2026-02-13 |
| 3. Belief Store | 3/3 | ✓ Complete | 2026-02-13 |
| 4. Convergence Detection | 0/TBD | Not started | - |
| 5. Meta-Comprehension | 0/TBD | Not started | - |
| 6. The Web | 0/TBD | Not started | - |
| 7. API Harness | 0/TBD | Not started | - |

---
*Roadmap reframed: 2026-02-13*
*Architecture: .planning/ARCHITECTURE_SKETCH.md*
*Total phases: 7 (3 complete, 4 remaining)*
