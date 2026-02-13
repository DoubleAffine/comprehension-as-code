# Roadmap: Comprehension-as-Code

## Overview

A computational theory of understanding. The roadmap follows the cognitive architecture:
primitives → operations → storage → emergence → integration.

Phase 1 (primitives) is complete. Remaining phases build the operations, memory model, and emergence conditions that make understanding computable.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Cognitive Primitives** - Define schemas for Observation, Comprehension, Confidence
- [ ] **Phase 2: Bayesian Update** - The core operation: observation + prior → posterior
- [ ] **Phase 3: Belief Store** - Persistence with memory efficiency (beliefs, not evidence)
- [ ] **Phase 4: Convergence Detection** - Notice "same shape" across domains (rising tide)
- [ ] **Phase 5: Meta-Comprehension** - Emergence conditions and crystallization
- [ ] **Phase 6: The Web** - Implicit connections, traversal, bootstrap
- [ ] **Phase 7: Agent Integration** - Working agent + meta-agent orchestration

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

### Phase 2: Bayesian Update
**Goal**: The core operation works: observations update beliefs, and the posterior IS the compression
**Depends on**: Phase 1
**Requirements**: Update operation, provenance tracking, observation lifecycle
**Success Criteria** (what must be TRUE):
  1. Given observation + existing comprehension → new posterior computed
  2. Confidence level updates based on evidence (confirming → higher, contradicting → lower)
  3. Provenance tracks which observations informed belief (references, not copies)
  4. Observations can be garbage collected after informing comprehension
  5. The update operation IS compression (no separate compress step)

**Plans:** 3 plans

Plans:
- [ ] 02-01-PLAN.md - Confidence transition state machine (TDD, Wave 1)
- [ ] 02-02-PLAN.md - Core Bayesian update operation (TDD, Wave 2)
- [ ] 02-03-PLAN.md - Observation lifecycle management (Wave 1)

### Phase 3: Belief Store
**Goal**: Comprehensions persist with memory efficiency; retrieval is by relevance, not "load all"
**Depends on**: Phase 2
**Requirements**: Persistence layer, retrieval, memory model
**Success Criteria** (what must be TRUE):
  1. Comprehensions persist across sessions
  2. Retrieval by domain, topic, confidence, recency
  3. Storage is beliefs (posteriors), not evidence (observations)
  4. Observation references are maintained; observation content can be pruned
  5. Storage grows with understanding, not with evidence count

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

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

### Phase 7: Agent Integration
**Goal**: Working agents query and update understanding; meta-agent observes and crystallizes
**Depends on**: Phase 6
**Requirements**: Working agent protocol, meta-agent, observation flow
**Success Criteria** (what must be TRUE):
  1. Working agent: queries relevant comprehension before acting
  2. Working agent: records observations during execution
  3. Working agent: updates comprehension after task (Bayesian update)
  4. Meta-agent: observes comprehension accumulation (not execution)
  5. Meta-agent: detects convergence, triggers crystallization
  6. Full loop: experience → observation → comprehension → meta-comprehension → bootstrap

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
| 2. Bayesian Update | 0/3 | Planned | - |
| 3. Belief Store | 0/TBD | Not started | - |
| 4. Convergence Detection | 0/TBD | Not started | - |
| 5. Meta-Comprehension | 0/TBD | Not started | - |
| 6. The Web | 0/TBD | Not started | - |
| 7. Agent Integration | 0/TBD | Not started | - |

---
*Roadmap reframed: 2026-02-13*
*Architecture: .planning/ARCHITECTURE_SKETCH.md*
*Total phases: 7 (1 complete, 6 remaining)*
