# Comprehension-as-Code

## What This Is

A system where comprehension is the primary artifact, not code. AI agents build and maintain verified understanding models before acting. A dedicated meta-agent observes all work, extracts learnings (especially from mistakes), and accumulates knowledge across projects. Agents bootstrap from this comprehension rather than starting fresh.

## Core Value

Agents must demonstrate verified understanding before acting—comprehension is inspectable, auditable, and compounds over time.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Define comprehension format that agents can read and write
- [ ] Build meta-agent that observes working agents and extracts learnings
- [ ] Implement selective recording (filter for important observations)
- [ ] Create abstraction layers (concrete → pattern → principle → meta)
- [ ] Build compression mechanism that preserves essence
- [ ] Implement cross-project accumulation
- [ ] Create verification system for comprehension claims
- [ ] Design checkpoint system (learn from mistakes without propagating them)

### Out of Scope

- Numeric Bayesian probabilities — language-based confidence, not math
- Human-first interface — primary consumer is agents, not humans
- Per-project isolation — this is explicitly cross-project

## Context

**Origin:** Exploring optimal AI coding workflows led to questioning whether "context files" are the right primitive. Insight: what if comprehension itself—not code—was the artifact? This connects to Bayesian epistemology (priors from LLM training, observations from work, posteriors as updated understanding) but expressed in natural language.

**Key insight on mistakes:** Errors are where learning comes from. The meta-agent should observe everything including mistakes, but checkpoints prevent wrong understanding from propagating into more bad work.

**Related work discovered:**
- "Context Engineering" — JetBrains treating context as first-class system
- "Compound Engineering" — persistent context files that accumulate
- "Memory Bank Protocol" (Cline) — hierarchical files solving memory reset
- Knowledge graph approaches (MegaMemory, etc.)

**Gap we're filling:** Existing approaches treat knowledge as supplementary to execution. We're making verified understanding the primary artifact, with code as downstream output.

## Constraints

- **Format**: Must be readable/writable by AI agents (primary consumer)
- **Philosophy**: Bayesian structure (prior → observation → posterior) but in language
- **Metacognition**: System must know what it knows, doesn't know, and confidence levels
- **Selectivity**: Cannot record everything—must filter for signal (surprising, costly, transferable)
- **Abstraction balance**: Compress toward principles but not so much that essence is lost

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Language over numbers for confidence | LLMs work in language; numeric precision would be false precision | — Pending |
| Full system for v1 | User wants complete vision, not incremental MVP | — Pending |
| Agents as primary consumer | Optimizes format for machine consumption, not human readability | — Pending |
| Observe mistakes, checkpoint actions | Mistakes are learning; checkpoints prevent propagation | — Pending |
| Let contradiction handling emerge | Don't prescribe—see what works in practice | — Pending |

---
*Last updated: 2025-02-13 after initialization*
