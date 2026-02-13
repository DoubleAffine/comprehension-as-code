# Requirements: Comprehension-as-Code

**Defined:** 2026-02-13
**Updated:** 2026-02-13 (architecture reframing)
**Core Value:** Understanding is computation. Agents don't just *have* understanding—they *run* it.

## v1 Requirements

Requirements aligned to the cognitive architecture:
Experience → Observation → Comprehension → Meta-comprehension → The Web

### Cognitive Primitives

- [x] **PRIM-01**: Observation schema captures ephemeral events with temporal metadata
- [x] **PRIM-02**: Comprehension schema has Bayesian structure (prior/posterior)
- [x] **PRIM-03**: Confidence levels defined in natural language (not numeric probabilities)
- [x] **PRIM-04**: Clear distinction between observations (events) and comprehension (beliefs)

### Bayesian Update

- [ ] **UPDATE-01**: Given observation + existing comprehension → new posterior computed
- [ ] **UPDATE-02**: Confidence updates based on evidence (confirming → higher, contradicting → lower)
- [ ] **UPDATE-03**: Provenance tracks which observations informed belief (references, not copies)
- [ ] **UPDATE-04**: Observations can be garbage collected after informing comprehension
- [ ] **UPDATE-05**: The posterior IS the compression (no separate compress step)

### Belief Store

- [ ] **STORE-01**: Comprehensions persist across sessions
- [ ] **STORE-02**: Retrieval by domain, topic, confidence, recency
- [ ] **STORE-03**: Storage is beliefs (posteriors), not evidence (observations)
- [ ] **STORE-04**: Storage grows with understanding, not with evidence count

### Convergence Detection

- [ ] **CONV-01**: Each new comprehension can query "what does this remind me of?"
- [ ] **CONV-02**: Similarity is structural (same shape), not keyword-based
- [ ] **CONV-03**: System tracks where comprehension density is building
- [ ] **CONV-04**: Candidate patterns emerge from repeated structure (rising tide)

### Meta-Comprehension

- [ ] **META-01**: Emergence conditions defined (min instances, domain diversity, confidence threshold)
- [ ] **META-02**: Meta-confidence computed from instance confidences
- [ ] **META-03**: Crystallization: when threshold met, pattern becomes named meta-comprehension
- [ ] **META-04**: New comprehensions recognized as "another instance of pattern X"

### The Web

- [ ] **WEB-01**: Connections exist through structural similarity (implicit, not explicit edges)
- [ ] **WEB-02**: From one comprehension, find related comprehensions (traversal)
- [ ] **WEB-03**: From meta-comprehension, access instances (navigation)
- [ ] **WEB-04**: Understanding is the web, not a list of documents

### Agent Integration

- [ ] **AGENT-01**: Working agent queries relevant comprehension before acting
- [ ] **AGENT-02**: Working agent records observations during execution
- [ ] **AGENT-03**: Working agent updates comprehension after task (Bayesian update)
- [ ] **AGENT-04**: Meta-agent observes comprehension accumulation (not execution)
- [ ] **AGENT-05**: Meta-agent detects convergence, triggers crystallization
- [ ] **AGENT-06**: Bootstrap: new agents load accumulated understanding

## Key Design Principles

These principles constrain implementation. Violating them is a defect.

| Principle | Meaning |
|-----------|---------|
| **Posterior IS compression** | No separate compression step; belief update compresses evidence into understanding |
| **Rising tide emergence** | Patterns become obvious through accumulation (Grothendieck); don't force abstraction |
| **Patterns between patterns** | The best abstraction notices analogies between theories (Banach) |
| **Memory efficiency** | Store beliefs, not evidence; observations are ephemeral, comprehensions persist |
| **Language confidence** | Natural language levels (HIGH/MEDIUM/LOW/UNKNOWN), not numeric probabilities |
| **Implicit web** | Connections exist because structures are similar, not because we drew edges |

## Out of Scope

Explicitly excluded to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Numeric Bayesian probabilities | Language-based confidence; LLMs work in language, not math |
| Forced abstraction pipeline | Rising tide: emergence, not construction |
| Human-first interface | Primary consumer is agents; optimize for machine consumption |
| Per-project isolation | Understanding accumulates across projects |
| Explicit graph construction | The web is implicit in structural similarity |
| Real-time observation | Batch/checkpoint-based sufficient for v1 |

## Traceability

Requirements mapped to roadmap phases.

| Phase | Requirements |
|-------|-------------|
| 1. Cognitive Primitives ✓ | PRIM-01, PRIM-02, PRIM-03, PRIM-04 |
| 2. Bayesian Update | UPDATE-01, UPDATE-02, UPDATE-03, UPDATE-04, UPDATE-05 |
| 3. Belief Store | STORE-01, STORE-02, STORE-03, STORE-04 |
| 4. Convergence Detection | CONV-01, CONV-02, CONV-03, CONV-04 |
| 5. Meta-Comprehension | META-01, META-02, META-03, META-04 |
| 6. The Web | WEB-01, WEB-02, WEB-03, WEB-04 |
| 7. Agent Integration | AGENT-01 through AGENT-06 |

**Coverage:**
- Total requirements: 27
- Phase 1 (complete): 4/4
- Remaining: 23

---
*Aligned with cognitive architecture: 2026-02-13*
*Reference: .planning/ARCHITECTURE_SKETCH.md*
