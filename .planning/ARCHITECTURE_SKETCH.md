# Cognitive Architecture Sketch

## Core Insight

Understanding is not documentation. It's a computational process with:
- State (beliefs)
- Operations (Bayesian update, convergence detection)
- Emergence (patterns crystallize through accumulation)

## The Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    THE WEB (emergent)                       │
│         Understanding as interconnected structure           │
│                                                             │
│    Patterns ←→ Patterns ←→ Patterns ←→ Patterns            │
│         ↑           ↑           ↑           ↑               │
└─────────┼───────────┼───────────┼───────────┼───────────────┘
          │           │           │           │
┌─────────┼───────────┼───────────┼───────────┼───────────────┐
│         ▼           ▼           ▼           ▼               │
│   META-COMPREHENSION (crystallizes when confidence HIGH)    │
│                                                             │
│   "These N comprehensions share the same structure"         │
│   - emerges from convergence, not constructed               │
│   - Bayesian confidence over instances                      │
│   - IS the abstraction (pattern between patterns)           │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ convergence detection
                          │ (same shape appearing repeatedly)
                          │
┌─────────────────────────────────────────────────────────────┐
│                 COMPREHENSION (persistent)                   │
│                                                             │
│   Belief state = compressed form of all evidence            │
│   - prior: what was believed                                │
│   - posterior: what is now believed                         │
│   - confidence: grows with evidence                         │
│   - provenance: which observations (references, not copies) │
│                                                             │
│   The posterior IS the compression.                         │
│   No separate "compress" step needed.                       │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ Bayesian update
                          │ (observation informs belief)
                          │
┌─────────────────────────────────────────────────────────────┐
│                 OBSERVATION (ephemeral)                      │
│                                                             │
│   Raw event with timestamp, source, context                 │
│   - captured in the moment                                  │
│   - informs comprehension via Bayesian update               │
│   - can be garbage collected after informing belief         │
│   - light storage: just enough to update                    │
└─────────────────────────────────────────────────────────────┘
                          ↑
                          │ selective recording
                          │ (signal, not noise)
                          │
┌─────────────────────────────────────────────────────────────┐
│                    EXPERIENCE (raw)                          │
│                                                             │
│   Agent execution, tool calls, responses, errors            │
│   - most is discarded                                       │
│   - only surprising/important becomes observation           │
└─────────────────────────────────────────────────────────────┘
```

## The Operations

### 1. Selective Recording
```
Experience → Observation (when worth recording)

Filter: Is this surprising? Costly? Transferable?
- Expected outcome → discard
- Surprising outcome → record
- Error/failure → always record
- Confirms rare pattern → record
```

### 2. Bayesian Update
```
Observation + Prior → Posterior

The update IS the compression:
- Don't store observation content in comprehension
- Store: "obs-017 raised confidence from MEDIUM to HIGH"
- The posterior encodes what all observations taught

Observations become references, then garbage collectible.
```

### 3. Convergence Detection
```
Comprehension₁ + Comprehension₂ + ... → Notice: "same shape"

Not searching. Noticing.
- Each new comprehension asks: "what does this remind me of?"
- Similarity is structural, not keyword
- When N domains show same structure → candidate for meta

Rising tide: accumulation creates conditions for recognition.
```

### 4. Meta-Comprehension Crystallization
```
Candidate pattern + HIGH confidence → Meta-comprehension

Emergence, not construction:
- "Retry with backoff" appears in API, DB, queue, file I/O
- Each instance is a comprehension with its own confidence
- Meta-confidence = f(instance confidences, domain diversity)
- When meta-confidence crosses threshold → crystallize

The pattern was always there. We just noticed.
```

## Memory Model

### What's stored:

| Layer | Storage | Lifetime | Size |
|-------|---------|----------|------|
| Experience | None (streams through) | Momentary | - |
| Observation | References + minimal context | Until belief updated | Small |
| Comprehension | Full belief state | Persistent | Medium |
| Meta-comprehension | Pattern + instances | Persistent | Small |

### Memory efficiency:

The key insight: **the posterior is the compression**.

Traditional: Store evidence, compress later
Ours: Update belief, discard evidence

An agent with 1000 observations doesn't store 1000 documents.
It stores the beliefs those observations produced.

### Retrieval:

Not "load all context." Instead:
- Query by domain, topic, confidence
- Load relevant comprehensions
- Meta-comprehensions provide shortcuts (load the pattern, not 50 instances)
- The web enables traversal (related comprehensions)

## The Rising Tide Model

Grothendieck: Don't attack the problem. Raise the water level until it dissolves.

Applied:
1. Keep recording comprehensions (don't over-filter)
2. Each comprehension positions itself relative to others (what does this remind me of?)
3. Density accumulates in domains of activity
4. Patterns become undeniable through repetition
5. Meta-comprehension crystallizes when confidence is high
6. The abstraction wasn't "found" - it became obvious

### No explicit "abstract now" step

The abstraction pipeline isn't:
```
concrete → pattern → principle (forced)
```

It's:
```
comprehension accumulates
→ same shapes keep appearing
→ confidence in pattern grows
→ pattern becomes named (meta-comprehension)
→ new instances recognized as "another case of X"
```

The water rises. The shell softens. The nut opens.

## Conditions for Emergence (Bayesian)

When does meta-comprehension crystallize?

```yaml
emergence_conditions:
  min_instances: 3  # at least 3 domains showing pattern
  min_diversity: 2  # from at least 2 different domains
  min_instance_confidence: medium  # each instance at least MEDIUM
  meta_confidence_threshold: high  # when to name it

  # Meta-confidence computation (sketch):
  # - Each instance contributes based on its confidence
  # - Domain diversity multiplies confidence
  # - Recency-weighted (recent instances count more?)
  # - Counter-evidence decreases confidence
```

This is Bayesian:
- Prior: "This might be a general pattern" (LOW)
- Evidence: Each instance in a new domain
- Posterior: Updated confidence in pattern generality
- Crystallization: When posterior reaches HIGH

## API Harness Integration

### The Harness Model

Understanding is automatic, not opt-in. Instead of agents explicitly calling tools to query/update beliefs, a harness layer intercepts all model interactions:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│         (Claude Code, API calls, Web interface)              │
└─────────────────────────────────────────────────────────────┘
                            ↓ request
┌─────────────────────────────────────────────────────────────┐
│                 COMPREHENSION HARNESS                        │
│                                                              │
│  INBOUND:                                                    │
│  1. Intercept prompt                                         │
│  2. Extract domain/topic signals                             │
│  3. Query relevant comprehensions from BeliefStore           │
│  4. Enrich prompt with belief context                        │
│  5. Forward enriched prompt to model                         │
│                                                              │
│  OUTBOUND:                                                   │
│  6. Receive response                                         │
│  7. Extract observations from interaction                    │
│  8. Run Bayesian updates on affected comprehensions          │
│  9. Run convergence detection (async/batched)                │
│  10. Persist updated beliefs                                 │
│  11. Return original response to client                      │
└─────────────────────────────────────────────────────────────┘
                            ↓ enriched request
┌─────────────────────────────────────────────────────────────┐
│                    ANTHROPIC API                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Properties

**Automatic:** Every interaction builds understanding without explicit action
**Transparent:** Client doesn't know harness exists; response unchanged
**Continuous:** Understanding accumulates across all sessions, all interfaces
**Implicit:** The meta-agent role is absorbed—convergence detection runs in harness update cycle

### Harness Components

1. **Request Interceptor** - Captures incoming prompts
2. **Belief Enricher** - Queries relevant comprehensions, injects as context
3. **Observation Extractor** - Identifies noteworthy patterns in interaction
4. **Update Engine** - Runs Bayesian updates (Phase 2)
5. **Convergence Detector** - Checks for structural similarity (Phase 4)
6. **Crystallizer** - Creates meta-comprehensions when thresholds met (Phase 5)

### Bootstrap via Harness

New conversation/session:
1. Harness extracts domain signals from first prompt
2. Queries relevant meta-comprehensions (high-level patterns)
3. Queries domain-specific comprehensions
4. Enriches prompt with accumulated priors
5. Model starts informed, not blank
6. Rising tide continues from current water level

## Open Questions

1. **Structural similarity** - How do we detect "same shape" across domains? Embedding? Schema matching? LLM judgment?

2. **Forgetting** - What decays? Observations yes. Comprehensions with no recent confirmation? Meta-comprehensions that stop getting instances?

3. **Contradiction** - When comprehensions conflict, is that signal (domain boundary) or noise (one is wrong)?

4. **Computational cost** - Convergence detection on every new comprehension? Or batch? Or triggered by density?

5. **Provenance depth** - How much of "why I believe this" to retain? Enough to debug, not so much it bloats.

---

*This is the architecture we're implementing. Understanding as computation.*
