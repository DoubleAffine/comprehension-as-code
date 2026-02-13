# Comprehension-as-Code

## What This Is

A computational theory of understanding, implemented as executable code.

Understanding is not documentation. It's a process with state (beliefs), operations (Bayesian update), and emergence (patterns crystallize through accumulation). This system makes understanding computable, inspectable, and transferable between agents.

The posterior IS the compression. The rising tide IS the abstraction. The web IS the understanding.

## Core Value

**Understanding is computation.**

Agents don't just *have* understanding—they *run* it. Beliefs are state. Updates are operations. Patterns emerge through accumulation, not construction.

## Architecture

See: `.planning/ARCHITECTURE_SKETCH.md`

```
Experience (raw, discarded)
    ↓ selective recording
Observation (ephemeral)
    ↓ Bayesian update (compression happens here)
Comprehension (persistent belief state)
    ↓ convergence detection (rising tide)
Meta-comprehension (emergent pattern)
    ↓ accumulation
The Web (interconnected understanding)
```

### Key Principles

1. **The posterior is the compression** — Don't store evidence, store what evidence taught. The belief state encodes all prior observations.

2. **Rising tide, not forced abstraction** — Patterns become obvious through repetition. Don't search for patterns. Let them become undeniable.

3. **Emergence through accumulation** — Meta-comprehension crystallizes when the same structure appears across domains with high confidence. It's not constructed, it's noticed.

4. **Memory efficiency through belief update** — 1000 observations become beliefs, not 1000 documents. Observations are ephemeral; comprehensions persist.

5. **The web is implicit** — Connections exist because structures are similar, not because we drew edges. Understanding is the pattern of patterns.

## Requirements

### Validated

- ✓ COMP-06: System defines clear format for comprehension vs observations — *Phase 1 complete*

### Active

**Cognitive primitives:**
- [ ] Observation schema (ephemeral events)
- [ ] Comprehension schema (persistent beliefs with Bayesian structure)
- [ ] Meta-comprehension schema (emergent patterns)

**Operations:**
- [ ] Selective recording (filter experience → observation)
- [ ] Bayesian update (observation + prior → posterior)
- [ ] Convergence detection (notice "same shape" across domains)
- [ ] Crystallization (pattern → meta-comprehension when confidence HIGH)

**Memory model:**
- [ ] Observation garbage collection (after informing belief)
- [ ] Comprehension persistence (belief state)
- [ ] Retrieval by relevance (not "load all")

**Integration (API Harness):**
- [ ] Request interception (capture all model API calls)
- [ ] Belief enrichment (query relevant comprehensions, inject as context)
- [ ] Observation extraction (identify noteworthy patterns in interactions)
- [ ] Automatic updates (Bayesian update + convergence detection, no explicit calls)
- [ ] Bootstrap (new sessions start with accumulated understanding)

### Out of Scope

- Numeric Bayesian probabilities — confidence in language, not math
- Forced abstraction pipeline — emergence, not construction
- Human-first interface — agents are primary consumer
- Per-project isolation — understanding accumulates across projects
- Explicit graph construction — the web is implicit in structural similarity

## Context

**Origin:** Started as "verified context files for agents." Evolved through:
1. Bayesian framing (priors, posteriors, confidence)
2. Meta-agent observation
3. Selective recording and abstraction layers
4. Grothendieck's rising tide (emergence through accumulation)
5. Recognition: this is a computational theory of understanding

**Banach's insight:** "A mathematician is a person who can find analogies between theorems; a better mathematician is one who can see analogies between proofs and the best mathematician can notice analogies between theories."

We're building the third level: patterns between patterns.

**Grothendieck's method:** Don't attack the problem. Raise the water level until it dissolves. Abstraction isn't forced—it becomes obvious through accumulation.

**API Harness model (2026-02-13):** Understanding is automatic, not opt-in. Instead of agents explicitly calling tools to query/update beliefs, a harness layer intercepts all model API calls. Every interaction enriches prompts with relevant beliefs and extracts observations for Bayesian update. Understanding accumulates continuously across all sessions and interfaces.

## Constraints

- **Bayesian structure** — Prior → observation → posterior, in natural language
- **Memory efficiency** — The posterior IS compression; don't store evidence
- **Emergence over construction** — Rising tide, not pattern search
- **Agent-consumable** — Primary consumer is AI agents bootstrapping
- **Metacognition** — System knows what it knows and how confident

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Language over numbers for confidence | LLMs work in language; precision would be false | ✓ Good |
| Posterior as compression | No separate compression step; belief update IS compression | — Pending |
| Rising tide emergence | Don't force abstraction; let patterns become obvious | — Pending |
| Observations ephemeral | Garbage collect after informing belief; memory efficiency | — Pending |
| Structural similarity for convergence | Detect "same shape" not "same keywords" | — Pending |
| Agents as primary consumer | Format optimized for machine consumption | ✓ Good |

## Phase 1 Status

Completed:
- Observation schema (Pydantic)
- Comprehension schema with Bayesian structure (prior/posterior)
- ConfidenceLevel enum (HIGH/MEDIUM/LOW/UNKNOWN)
- Format specifications
- Sample documents
- Parser and validation tests

These are valid primitives. The architecture above builds on them.

---
*Last updated: 2026-02-13 after architecture reframing*
*Reference: .planning/ARCHITECTURE_SKETCH.md*
