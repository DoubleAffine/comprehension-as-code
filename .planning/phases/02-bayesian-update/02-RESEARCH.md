# Phase 2: Bayesian Update - Research

**Researched:** 2026-02-13
**Domain:** Bayesian belief updates in natural language, provenance tracking, observation lifecycle
**Confidence:** MEDIUM-HIGH

## Summary

Phase 2 implements the core belief update operation: given an observation and existing comprehension, compute a new posterior. This is the central "compression" operation of the system—the posterior IS the compression, not a separate step. The key insight is that we update beliefs and discard evidence rather than storing evidence and compressing later.

The recommended approach uses **Pydantic's immutable pattern** (`model_copy(update=...)`) for belief state transitions, **reference-based provenance** (observation IDs, not content), and **language-based confidence transitions** following defined rules. The update operation should be a pure function: `(Observation, Comprehension) -> Comprehension'` where the new comprehension has an updated posterior reflecting the observation's impact.

Natural language Bayesian updates are "Bayesian-inspired" rather than mathematically rigorous—this is a design choice from Phase 1. The focus is on systematic belief evolution with explicit reasoning, not probabilistic calculus.

**Primary recommendation:** Implement `update_comprehension(observation: Observation, comprehension: Comprehension) -> Comprehension` as a pure function that produces a new Comprehension with updated posterior. Use immutable patterns throughout. Design confidence transitions as a simple state machine with explicit rules. Track provenance as observation ID references that enable garbage collection.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.x | Schema validation + immutable updates | `model_copy(update=...)` provides immutable state transitions; already in use from Phase 1 |
| python-frontmatter | 1.x | Markdown parsing | Already established in Phase 1 for document I/O |
| datetime | stdlib | Timestamp handling | Standard library; no external dependency needed |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uuid | stdlib | Generate observation/comprehension IDs | When creating new documents |
| typing | stdlib | Type hints for function signatures | All module interfaces |
| enum | stdlib | Confidence level definitions | Already used from Phase 1 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic immutable updates | Dataclass with `replace()` | Dataclass is lighter but loses Pydantic validation on update |
| Pure function updates | Mutable state machine | Mutable is simpler short-term but harder to test/debug |
| Reference-based provenance | Embedded observation content | Embedding defeats memory efficiency goal; references enable GC |

**Installation:**
```bash
# No new dependencies required - using Phase 1 stack
uv pip install pydantic pyyaml python-frontmatter
```

## Architecture Patterns

### Recommended Project Structure

```
src/comprehension/
├── schema/                    # Phase 1 (existing)
│   ├── observation.py
│   ├── comprehension.py
│   └── confidence.py
├── update/                    # Phase 2 (new)
│   ├── __init__.py
│   ├── bayesian_update.py     # Core update function
│   ├── confidence_rules.py    # Confidence transition logic
│   ├── provenance.py          # Reference tracking
│   └── lifecycle.py           # Observation lifecycle management
├── parser/                    # Phase 1 (existing)
│   └── markdown_parser.py
└── __init__.py
```

### Pattern 1: Pure Function Belief Update

**What:** Update operation as a pure function that takes observation + comprehension and returns new comprehension
**When to use:** Always—this is the core Phase 2 operation
**Example:**

```python
# Source: Pydantic model_copy pattern for immutable updates
from comprehension.schema import Comprehension, Observation, BeliefPosterior, ConfidenceLevel
from datetime import datetime

def update_comprehension(
    observation: Observation,
    comprehension: Comprehension,
    update_reasoning: str
) -> Comprehension:
    """Apply observation to comprehension, producing new posterior.

    The posterior IS the compression—this function compresses
    observation evidence into belief state update.

    Args:
        observation: New evidence to incorporate
        comprehension: Existing belief state
        update_reasoning: Explanation of how observation changes belief

    Returns:
        New Comprehension with updated posterior, version, timestamp
    """
    # Compute new confidence based on evidence type
    new_confidence = compute_confidence_transition(
        current=comprehension.posterior.confidence,
        observation=observation,
        prior=comprehension.prior
    )

    # Create new posterior (immutable)
    new_posterior = BeliefPosterior(
        statement=comprehension.posterior.statement,  # May be updated by caller
        confidence=new_confidence,
        update_reasoning=update_reasoning,
        observations_used=comprehension.posterior.observations_used + [observation.id]
    )

    # Return new comprehension (immutable copy with updates)
    return comprehension.model_copy(update={
        "posterior": new_posterior,
        "observations": comprehension.observations + [observation.id],
        "updated": datetime.now(),
        "version": comprehension.version + 1
    })
```

### Pattern 2: Confidence Transition State Machine

**What:** Define explicit rules for how confidence levels change based on evidence
**When to use:** Every update operation
**Example:**

```python
# Source: Project design principles (natural language confidence)
from enum import Enum
from typing import Tuple

class EvidenceType(str, Enum):
    """Classification of how observation relates to belief."""
    CONFIRMING = "confirming"      # Supports existing belief
    CONTRADICTING = "contradicting" # Challenges existing belief
    NEUTRAL = "neutral"            # Doesn't clearly support or contradict
    NOVEL = "novel"                # About something not in current belief

# Confidence transition rules
# Format: (current_confidence, evidence_type) -> new_confidence
CONFIDENCE_TRANSITIONS: dict[Tuple[ConfidenceLevel, EvidenceType], ConfidenceLevel] = {
    # From UNKNOWN
    (ConfidenceLevel.UNKNOWN, EvidenceType.CONFIRMING): ConfidenceLevel.LOW,
    (ConfidenceLevel.UNKNOWN, EvidenceType.CONTRADICTING): ConfidenceLevel.LOW,  # Still low, but different direction
    (ConfidenceLevel.UNKNOWN, EvidenceType.NEUTRAL): ConfidenceLevel.UNKNOWN,

    # From LOW
    (ConfidenceLevel.LOW, EvidenceType.CONFIRMING): ConfidenceLevel.MEDIUM,
    (ConfidenceLevel.LOW, EvidenceType.CONTRADICTING): ConfidenceLevel.LOW,  # Stay low, belief may flip
    (ConfidenceLevel.LOW, EvidenceType.NEUTRAL): ConfidenceLevel.LOW,

    # From MEDIUM
    (ConfidenceLevel.MEDIUM, EvidenceType.CONFIRMING): ConfidenceLevel.HIGH,
    (ConfidenceLevel.MEDIUM, EvidenceType.CONTRADICTING): ConfidenceLevel.LOW,
    (ConfidenceLevel.MEDIUM, EvidenceType.NEUTRAL): ConfidenceLevel.MEDIUM,

    # From HIGH
    (ConfidenceLevel.HIGH, EvidenceType.CONFIRMING): ConfidenceLevel.HIGH,  # Already max
    (ConfidenceLevel.HIGH, EvidenceType.CONTRADICTING): ConfidenceLevel.MEDIUM,
    (ConfidenceLevel.HIGH, EvidenceType.NEUTRAL): ConfidenceLevel.HIGH,
}

def compute_confidence_transition(
    current: ConfidenceLevel,
    evidence_type: EvidenceType
) -> ConfidenceLevel:
    """Apply confidence transition rule."""
    return CONFIDENCE_TRANSITIONS.get(
        (current, evidence_type),
        current  # Default: no change
    )
```

### Pattern 3: Reference-Based Provenance

**What:** Store observation IDs as references, not observation content
**When to use:** All comprehension documents
**Example:**

```python
# Source: Project architecture (memory efficiency principle)
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass(frozen=True)
class ProvenanceRecord:
    """Tracks which observations informed a belief update.

    Key insight: We store references (IDs), not content.
    This enables garbage collection of observations after
    they've informed comprehension.
    """
    observation_id: str
    update_timestamp: datetime
    evidence_type: EvidenceType
    confidence_before: ConfidenceLevel
    confidence_after: ConfidenceLevel

class ProvenanceTracker:
    """Manages provenance references for a comprehension."""

    def __init__(self, comprehension_id: str):
        self.comprehension_id = comprehension_id
        self.records: List[ProvenanceRecord] = []

    def record_update(
        self,
        observation_id: str,
        evidence_type: EvidenceType,
        confidence_before: ConfidenceLevel,
        confidence_after: ConfidenceLevel
    ) -> None:
        """Record that an observation informed this comprehension."""
        self.records.append(ProvenanceRecord(
            observation_id=observation_id,
            update_timestamp=datetime.now(),
            evidence_type=evidence_type,
            confidence_before=confidence_before,
            confidence_after=confidence_after
        ))

    def get_observation_ids(self) -> List[str]:
        """Get all observation IDs that informed this comprehension."""
        return [r.observation_id for r in self.records]

    def can_garbage_collect(self, observation_id: str) -> bool:
        """Check if observation has been incorporated into belief."""
        return observation_id in self.get_observation_ids()
```

### Pattern 4: Observation Lifecycle Management

**What:** Track observation state from creation through incorporation to garbage collection
**When to use:** Managing observation retention
**Example:**

```python
# Source: Project architecture (observations are ephemeral)
from enum import Enum
from typing import Set

class ObservationState(str, Enum):
    """Lifecycle states for observations."""
    PENDING = "pending"        # Created, not yet incorporated
    INCORPORATED = "incorporated"  # Has informed at least one comprehension
    COLLECTIBLE = "collectible"    # Safe to garbage collect

class ObservationLifecycle:
    """Manages observation lifecycle for garbage collection.

    Key insight: Once an observation has informed comprehension,
    the observation itself can be discarded. The posterior IS
    the compression—we store beliefs, not evidence.
    """

    def __init__(self):
        self._pending: Set[str] = set()
        self._incorporated: Set[str] = set()

    def register(self, observation_id: str) -> None:
        """Register new observation as pending."""
        self._pending.add(observation_id)

    def mark_incorporated(self, observation_id: str) -> None:
        """Mark observation as having informed a comprehension."""
        self._pending.discard(observation_id)
        self._incorporated.add(observation_id)

    def get_collectible(self) -> Set[str]:
        """Get observation IDs safe for garbage collection.

        Returns observations that have been incorporated into
        at least one comprehension's posterior.
        """
        return self._incorporated.copy()

    def collect(self, observation_id: str) -> bool:
        """Remove observation from tracking (after deletion).

        Returns True if observation was collectible.
        """
        if observation_id in self._incorporated:
            self._incorporated.remove(observation_id)
            return True
        return False
```

### Anti-Patterns to Avoid

- **Mutable belief state:** Modifying comprehension in place rather than creating new versions. Leads to lost history, difficult debugging, race conditions.

- **Embedded observation content:** Copying observation content into comprehension rather than referencing by ID. Defeats memory efficiency, prevents garbage collection.

- **Implicit confidence changes:** Changing confidence without explicit reasoning. Violates provenance tracking, makes updates opaque.

- **Order-dependent updates:** Different results based on observation order (when observations are independent). Violates Bayesian exchangeability property.

- **Unbounded observation retention:** Keeping all observations forever. The posterior IS the compression—observations should be collectible after incorporation.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Immutable updates | Manual dict copying | Pydantic `model_copy(update=...)` | Validates on copy, handles nested structures |
| ID generation | Custom ID schemes | `uuid.uuid4()` or timestamp-based | Standard, collision-free, sortable options |
| Timestamp handling | String manipulation | `datetime.now(timezone.utc)` | Timezone-aware, ISO-compliant |
| Confidence validation | String comparisons | `ConfidenceLevel` enum | Type-safe, exhaustive matching |

**Key insight:** Phase 2 is about the update *operation*, not data storage. Focus on pure functions that transform comprehension state. Storage is Phase 3's concern.

## Common Pitfalls

### Pitfall 1: Bayesian Theater (Form Without Function)

**What goes wrong:** Using Bayesian vocabulary (prior/posterior) without meaningful belief updates
**Why it happens:** Natural language "updates" can mask the fact that nothing actually changes
**How to avoid:**
- Test: contradicting evidence MUST decrease confidence
- Test: confirming evidence MUST increase confidence (until HIGH)
- Test: belief statement MUST change when evidence contradicts
- Implement explicit confidence transition rules (not just LLM judgment)
**Warning signs:** Posteriors identical to priors despite observations

### Pitfall 2: Lost Provenance

**What goes wrong:** Can't trace why a belief exists or which observations informed it
**Why it happens:** Provenance feels like metadata overhead; defer "until needed"
**How to avoid:**
- `observations_used` is required field on BeliefPosterior (Phase 1 schema)
- Every update records which observation triggered it
- Track confidence before/after for audit trail
**Warning signs:** "Why do we believe X?" has no answer

### Pitfall 3: Observation Content Leakage

**What goes wrong:** Observation content gets copied into comprehension, defeating memory efficiency
**Why it happens:** Easier to embed than reference; feels more "complete"
**How to avoid:**
- Store observation ID only, never content
- Comprehension can include reasoning that references observations
- Observation content lives only in observation document (until GC)
**Warning signs:** Comprehension documents grow linearly with observation count

### Pitfall 4: Non-Idempotent Updates

**What goes wrong:** Applying same observation twice changes result
**Why it happens:** No check for already-incorporated observations
**How to avoid:**
- Check if observation.id already in comprehension.observations before update
- Same observation applied twice = no change (idempotent)
- Track observation state in lifecycle manager
**Warning signs:** Duplicate observations inflate confidence

### Pitfall 5: Belief Statement Stagnation

**What goes wrong:** Confidence changes but belief statement never updates
**Why it happens:** Updating confidence is easier than updating natural language statement
**How to avoid:**
- When evidence contradicts, belief statement MUST change (not just confidence)
- Define clear rules: contradicting evidence → new statement required
- The statement IS the belief; confidence is meta about the statement
**Warning signs:** "high confidence in X" where X was contradicted by evidence

## Code Examples

### Core Update Operation

```python
# Source: Pydantic v2 documentation, project architecture
from comprehension.schema import Comprehension, Observation, BeliefPosterior, ConfidenceLevel
from comprehension.update.confidence_rules import EvidenceType, compute_confidence_transition
from datetime import datetime, timezone
from typing import Optional

def bayesian_update(
    observation: Observation,
    comprehension: Comprehension,
    evidence_type: EvidenceType,
    new_statement: Optional[str] = None,
    update_reasoning: str = ""
) -> Comprehension:
    """Apply Bayesian update: observation informs comprehension.

    This IS the compression operation. The new posterior encodes
    what the observation taught, allowing observation GC.

    Args:
        observation: Evidence to incorporate
        comprehension: Current belief state
        evidence_type: How observation relates to belief
        new_statement: Updated belief (required if contradicting)
        update_reasoning: Explanation of belief change

    Returns:
        New Comprehension with updated posterior

    Raises:
        ValueError: If contradicting evidence but no new statement
    """
    # Idempotency check
    if observation.id in comprehension.observations:
        return comprehension  # Already incorporated

    # Validate: contradicting evidence requires new statement
    if evidence_type == EvidenceType.CONTRADICTING and new_statement is None:
        raise ValueError(
            "Contradicting evidence requires updated belief statement"
        )

    # Compute confidence transition
    old_confidence = comprehension.posterior.confidence
    new_confidence = compute_confidence_transition(old_confidence, evidence_type)

    # Determine final statement
    final_statement = (
        new_statement
        if new_statement is not None
        else comprehension.posterior.statement
    )

    # Build update reasoning if not provided
    if not update_reasoning:
        update_reasoning = (
            f"Observation {observation.id} ({evidence_type.value}) "
            f"changed confidence from {old_confidence.value} to {new_confidence.value}"
        )

    # Create new posterior
    new_posterior = BeliefPosterior(
        statement=final_statement,
        confidence=new_confidence,
        update_reasoning=update_reasoning,
        observations_used=comprehension.posterior.observations_used + [observation.id]
    )

    # Return new comprehension (immutable)
    return comprehension.model_copy(update={
        "posterior": new_posterior,
        "observations": comprehension.observations + [observation.id],
        "updated": datetime.now(timezone.utc),
        "version": comprehension.version + 1
    })
```

### Evidence Type Classification

```python
# Source: Project design principles
from comprehension.schema import Observation, Comprehension
from comprehension.update.confidence_rules import EvidenceType

def classify_evidence(
    observation: Observation,
    comprehension: Comprehension
) -> EvidenceType:
    """Classify how observation relates to existing belief.

    This classification drives confidence updates.

    Note: In production, this might use LLM judgment.
    For Phase 2 MVP, can be explicit/manual classification.
    """
    # Check observation context for explicit classification
    evidence_hint = observation.context.get("evidence_type")
    if evidence_hint:
        return EvidenceType(evidence_hint)

    # Check if observation context indicates expectation mismatch
    expected = observation.context.get("expected")
    actual = observation.context.get("actual")

    if expected is not None and actual is not None:
        if expected == actual:
            return EvidenceType.CONFIRMING
        else:
            return EvidenceType.CONTRADICTING

    # Default to neutral if can't determine
    return EvidenceType.NEUTRAL
```

### Observation Garbage Collection

```python
# Source: Project architecture (memory efficiency)
from pathlib import Path
from typing import List, Set
from comprehension.update.lifecycle import ObservationLifecycle

def collect_observations(
    lifecycle: ObservationLifecycle,
    observation_dir: Path,
    dry_run: bool = True
) -> List[str]:
    """Garbage collect observations that have informed comprehension.

    Key insight: The posterior IS the compression. Once an observation
    has updated a belief, we no longer need the observation itself.

    Args:
        lifecycle: Tracks observation states
        observation_dir: Directory containing observation files
        dry_run: If True, report what would be deleted without deleting

    Returns:
        List of observation IDs that were (or would be) collected
    """
    collectible = lifecycle.get_collectible()
    collected: List[str] = []

    for obs_id in collectible:
        obs_file = observation_dir / f"{obs_id}.md"

        if obs_file.exists():
            if not dry_run:
                obs_file.unlink()
                lifecycle.collect(obs_id)
            collected.append(obs_id)

    return collected
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Numeric Bayesian probabilities | Natural language confidence levels | 2024-2025 | LLMs work better with language; avoids false precision |
| Store all observations | Posterior as compression (GC observations) | 2025-2026 | Memory efficiency for long-running agents |
| Mutable state updates | Immutable functional updates | 2024-2025 | Better debugging, versioning, concurrency |
| Monolithic belief documents | Modular comprehension with references | 2025 | Selective retrieval, manageable document size |

**Current innovations:**

- [Bayesian Teaching for LLMs](https://www.nature.com/articles/s41467-025-67998-6) - Teaching LLMs to mimic normative Bayesian updating improves belief evolution
- [Memory Evolution in LLM Agents](https://www.emergentmind.com/topics/memory-mechanisms-in-llm-based-agents) - New experiences refine existing knowledge, not just add to it
- [Pydantic v2 model_copy](https://docs.pydantic.dev/latest/concepts/models/) - Immutable update patterns with validation

**Deprecated/outdated:**
- Numeric probability tracking for natural language beliefs (false precision)
- Storing full observation content in comprehension (memory inefficient)
- Mutable state for belief tracking (loses history, race conditions)

## Open Questions

1. **Evidence type classification automation**
   - What we know: Phase 2 needs to classify observations as confirming/contradicting/neutral
   - What's unclear: Should this be LLM-judged, rule-based, or manual?
   - Recommendation: Start with explicit classification in observation context; add LLM classification in Phase 7 (agent integration)

2. **Multi-observation batch updates**
   - What we know: Single observation update is the primitive
   - What's unclear: Should batch updates be atomic? Order-independent?
   - Recommendation: Implement as sequential single updates; test exchangeability; batch atomicity can be Phase 3 (storage) concern

3. **Belief statement update generation**
   - What we know: Contradicting evidence requires updated statement
   - What's unclear: How to generate new statement from observation + old statement?
   - Recommendation: For Phase 2, require caller to provide new statement; LLM generation is Phase 7 enhancement

4. **Confidence transition rules**
   - What we know: Need explicit rules (not just LLM judgment)
   - What's unclear: Are the proposed transition rules optimal?
   - Recommendation: Start with simple rules; track transitions; refine based on observed behavior

## Sources

### Primary (HIGH confidence)

- [Pydantic v2 Models Documentation](https://docs.pydantic.dev/latest/concepts/models/) - `model_copy()` immutable update patterns
- [Pydantic Immutability Guide](https://cursa.app/en/page/immutability-freezing-and-controlled-mutation) - Frozen models, controlled mutation
- Phase 1 schemas (`/Users/ianphilipp/comprehension-as-code/src/comprehension/schema/`) - Existing data structures
- Phase 1 research (`/Users/ianphilipp/comprehension-as-code/.planning/phases/01-comprehension-format/01-RESEARCH.md`) - Format decisions

### Secondary (MEDIUM confidence)

- [Bayesian Teaching Enables Probabilistic Reasoning in LLMs](https://www.nature.com/articles/s41467-025-67998-6) - Bayesian update patterns for LLM systems
- [Memory Mechanisms in LLM Agents](https://www.emergentmind.com/topics/memory-mechanisms-in-llm-based-agents) - Memory evolution patterns
- [From Storage to Experience: LLM Agent Memory Survey](https://www.preprints.org/manuscript/202601.0618) - Trajectory refinement, confidence-weighted consolidation
- [Data Lineage and Provenance Tracking](https://softwarepatternslexicon.com/bitemporal-modeling/bi-temporal-data-warehouses/data-lineage-and-provenance-tracking/) - Provenance design patterns

### Tertiary (LOW confidence - project-specific)

- Project PITFALLS.md - Bayesian Theater anti-pattern, compound error accumulation
- Project ARCHITECTURE_SKETCH.md - Posterior as compression design principle
- Project REQUIREMENTS.md - UPDATE-01 through UPDATE-05 requirements

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing Phase 1 dependencies (Pydantic, python-frontmatter)
- Architecture patterns: MEDIUM-HIGH - Pure function updates, immutability patterns are well-established; confidence rules are project-specific design
- Pitfalls: HIGH - Derived from project PITFALLS.md research, particularly Bayesian Theater
- Code examples: MEDIUM - Patterns are sound; specific implementation may need refinement

**Research date:** 2026-02-13
**Valid until:** 60 days (stable patterns; implementation details may evolve during Phase 2)
