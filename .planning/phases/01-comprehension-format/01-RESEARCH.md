# Phase 1: Comprehension Format - Research

**Researched:** 2026-02-13
**Domain:** Knowledge representation, machine-readable specification formats, Bayesian belief structures
**Confidence:** MEDIUM-HIGH

## Summary

Phase 1 establishes the foundational format that distinguishes "comprehension" (structured understanding with Bayesian structure) from "raw observations" (events, traces, logs). This is a novel domain—no existing standard directly addresses "comprehension as artifact"—but adjacent standards (AGENTS.md, SKILL.md, Human Knowledge Markdown) and established patterns (Pydantic schemas, YAML frontmatter) provide strong foundations.

The recommended approach is **Markdown with YAML frontmatter**, validated against **Pydantic models**, with a clear separation between:
1. **Raw observations** (episodic events with timestamps and context)
2. **Comprehension** (structured beliefs with prior/observation/posterior Bayesian structure and confidence levels)

This format optimizes for AI agent consumption (primary user), git-versioning, token efficiency, and human readability (secondary benefit).

**Primary recommendation:** Define comprehension as YAML-frontmatter Markdown documents with Pydantic validation schemas. Use a clear type hierarchy: `observation` (raw event) vs `comprehension` (structured belief with Bayesian update history).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.x | Schema definition and validation | Industry standard for structured AI outputs; 300M+ monthly downloads; auto-generates JSON Schema |
| PyYAML | 6.x | YAML parsing/serialization | Standard Python YAML library; safe loading built-in |
| python-frontmatter | 1.x | Markdown+YAML parsing | Purpose-built for frontmatter extraction; widely used |
| jsonschema | 4.x | JSON Schema validation | Reference implementation; validates generated schemas |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ruamel.yaml | 0.18+ | Round-trip YAML editing | When preserving comments/formatting matters |
| Markform parser | N/A | Structured markdown forms | If implementing form-based comprehension capture |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Markdown+YAML | JSON-LD | JSON-LD: formal semantics, web interoperability; verbose, poor token efficiency, harder for humans |
| Pydantic | dataclasses + jsonschema | dataclasses: lighter; no validation, no auto-retry with LLMs |
| File-based | Database-first | Database: better querying; loses git-versioning, harder to bootstrap |

**Installation:**
```bash
uv pip install pydantic pyyaml python-frontmatter jsonschema
```

## Architecture Patterns

### Recommended Project Structure

```
comprehension-as-code/
├── src/
│   └── comprehension/
│       ├── schema/                    # Schema definitions
│       │   ├── __init__.py
│       │   ├── observation.py         # Raw observation models
│       │   ├── comprehension.py       # Comprehension models (Bayesian)
│       │   ├── confidence.py          # Confidence level definitions
│       │   └── validators.py          # Custom validators
│       ├── parser/                    # Parsing utilities
│       │   ├── __init__.py
│       │   ├── markdown_parser.py     # Frontmatter extraction
│       │   └── schema_generator.py    # JSON Schema export
│       └── __init__.py
├── spec/                              # Human-readable specifications
│   ├── COMPREHENSION_FORMAT.md        # Format specification document
│   ├── OBSERVATION_FORMAT.md          # Observation format spec
│   └── examples/                      # Sample documents
│       ├── sample_observation.md
│       └── sample_comprehension.md
└── tests/
    └── comprehension/
        ├── test_schema_validation.py
        └── test_sample_documents.py
```

### Pattern 1: Layered Schema Design

**What:** Separate schemas for observations vs comprehension, with comprehension building on observations
**When to use:** Always—this is the core distinction for the phase
**Example:**

```python
# Source: Pydantic AI documentation patterns
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime

class ConfidenceLevel(str, Enum):
    """Natural language confidence levels per project requirements."""
    HIGH = "high"      # Verified against behavior; multiple confirmations
    MEDIUM = "medium"  # Single confirmation; reasonable evidence
    LOW = "low"        # Tentative; needs validation
    UNKNOWN = "unknown"  # Explicitly uncertain

class Observation(BaseModel):
    """Raw observation—what happened, without interpretation."""
    id: str
    timestamp: datetime
    source: str  # Agent/system that made observation
    event: str   # What was observed
    context: dict = Field(default_factory=dict)
    trace_ref: Optional[str] = None  # Link to full trace

class BeliefPrior(BaseModel):
    """Prior belief before observation."""
    statement: str  # Natural language belief
    confidence: ConfidenceLevel
    source: str  # "training" | "accumulated" | "documentation"
    reasoning: Optional[str] = None

class BeliefPosterior(BaseModel):
    """Updated belief after observation(s)."""
    statement: str  # Natural language belief
    confidence: ConfidenceLevel
    update_reasoning: str  # How observations changed belief
    observations_used: List[str]  # References to observation IDs

class Comprehension(BaseModel):
    """Structured understanding with Bayesian update history."""
    id: str
    topic: str
    domain: str
    prior: BeliefPrior
    observations: List[str]  # Observation IDs
    posterior: BeliefPosterior
    created: datetime
    updated: datetime
    version: int = 1
    verified: bool = False  # Has behavioral verification passed?
```

### Pattern 2: Markdown + YAML Frontmatter Format

**What:** Store comprehension as human-readable Markdown with machine-readable YAML metadata
**When to use:** For persistent comprehension documents
**Example:**

```yaml
---
# Comprehension document frontmatter
spec: comprehension/v1
type: comprehension
id: comp-auth-api-001
topic: Authentication API behavior
domain: api-integration

prior:
  statement: "The authentication API uses REST endpoints for all operations"
  confidence: medium
  source: documentation
  reasoning: "Based on API documentation from project setup"

observations:
  - obs-001  # REST endpoint returned 404
  - obs-002  # GraphQL query succeeded

posterior:
  statement: "The authentication API uses GraphQL, not REST; documentation is outdated"
  confidence: high
  update_reasoning: "REST endpoint failure combined with GraphQL success indicates migration. Documentation not updated."
  observations_used: [obs-001, obs-002]

metadata:
  created: 2026-02-13T10:30:00Z
  updated: 2026-02-13T14:15:00Z
  version: 2
  verified: true
  verified_by: behavioral-test-auth-001
---

# Authentication API Behavior

## Summary

The authentication API uses **GraphQL** rather than REST endpoints, contrary to initial documentation.

## Evidence

1. REST endpoint `/api/auth/login` returned 404 (obs-001)
2. GraphQL mutation `authenticate` succeeded with same credentials (obs-002)

## Implications

- All authentication calls must use GraphQL client
- Documentation needs update
- Other API assumptions should be verified

## Related Comprehension

- [API Base URL Configuration](./comp-api-base-001.md)
```

### Pattern 3: Observation Document Format

**What:** Lighter-weight format for raw observations (events without interpretation)
**When to use:** For episodic memory capture before comprehension synthesis
**Example:**

```yaml
---
spec: observation/v1
type: observation
id: obs-001
timestamp: 2026-02-13T10:25:00Z
source: agent/api-integration-agent
trace_ref: trace-2026-02-13-10-25-abc123

event:
  action: http_request
  method: POST
  url: /api/auth/login

outcome:
  status: 404
  error: "Not Found"

context:
  project: example-project
  task: authenticate-user
  prior_belief: comp-auth-api-001/v1
---

# Observation: REST auth endpoint not found

Agent attempted POST to `/api/auth/login` and received 404.
```

### Anti-Patterns to Avoid

- **Mixing observations and comprehension:** Keep raw events separate from interpreted understanding. Observations are "what happened"; comprehension is "what we now believe."

- **Implicit confidence:** Always specify confidence level explicitly. "This is true" without confidence is ambiguous—does the agent know confidently or is it guessing?

- **Bayesian language without structure:** Using words like "prior" and "posterior" without actual structured fields for each. Either implement the structure or don't use the vocabulary.

- **Monolithic comprehension documents:** One massive document with all knowledge. Use modular, topic-focused documents that can be selectively retrieved.

- **Unversioned comprehension:** Comprehension evolves. Always version and track history of belief changes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema validation | Custom validation logic | Pydantic models | Type coercion, error messages, LLM retry integration |
| YAML parsing | Manual string parsing | PyYAML + python-frontmatter | Edge cases (multiline, escaping, unicode) are tricky |
| JSON Schema generation | Manual schema writing | Pydantic `.model_json_schema()` | Stays in sync with Python models automatically |
| Confidence level handling | Numeric probabilities | Enum with natural language labels | LLMs work better with language; project requirement |

**Key insight:** The format should be simple enough that most complexity lives in validation and parsing libraries, not custom code. Pydantic handles validation; frontmatter handles parsing; JSON Schema handles interoperability.

## Common Pitfalls

### Pitfall 1: Overloading Confidence Semantics

**What goes wrong:** Using "high/medium/low" without defining what each means operationally
**Why it happens:** Seems obvious, but interpretations vary between agents and over time
**How to avoid:** Define operationally:
- **HIGH:** Verified against behavior; would bet on it
- **MEDIUM:** Reasonable evidence; single confirmation
- **LOW:** Tentative; needs validation
- **UNKNOWN:** Explicitly uncertain; do not act on
**Warning signs:** Different agents assign different confidence levels to equivalent evidence

### Pitfall 2: Schema Drift

**What goes wrong:** Schema evolves but old documents don't migrate; validation starts failing
**Why it happens:** No versioning strategy; backward compatibility not considered
**How to avoid:**
- Include `spec` version in every document
- Design schema migrations before v1 ships
- Use Pydantic's `Field(deprecated=...)` for phased removal
**Warning signs:** Validation passes on new documents but fails on accumulated knowledge

### Pitfall 3: Token Bloat in Comprehension Documents

**What goes wrong:** Comprehension documents become so detailed they exceed context limits when bootstrapping
**Why it happens:** Including every observation inline; no summarization strategy
**How to avoid:**
- Reference observations by ID, don't embed full text
- Use progressive disclosure: summary in frontmatter, detail in body
- Measure token count per document; set limits
**Warning signs:** Bootstrap context exceeds 50% of token budget before task-specific context

### Pitfall 4: Missing Provenance

**What goes wrong:** Comprehension exists but nobody knows where it came from or why to trust it
**Why it happens:** Provenance feels like overhead; defer "until needed"
**How to avoid:**
- Require `source` on all priors
- Require `observations_used` on all posteriors
- Track `verified` and `verified_by` fields
**Warning signs:** Agent asks "why do we believe X?" and system can't answer

### Pitfall 5: Bayesian Theater

**What goes wrong:** Using prior/posterior language without actual belief update mechanics
**Why it happens:** Bayesian vocabulary sounds rigorous; implementing it is harder
**How to avoid:**
- Test: Does posterior actually change based on observations?
- Test: Does order of observations affect final belief (it shouldn't for exchangeable observations)?
- Accept that natural language "Bayesian" is Bayesian-inspired, not mathematically rigorous
**Warning signs:** Posteriors identical to priors despite contradictory observations

## Code Examples

### Parsing a Comprehension Document

```python
# Source: python-frontmatter documentation pattern
import frontmatter
from pydantic import ValidationError
from comprehension.schema import Comprehension

def load_comprehension(filepath: str) -> Comprehension:
    """Load and validate a comprehension document."""
    with open(filepath, 'r') as f:
        doc = frontmatter.load(f)

    # Frontmatter becomes the Pydantic model input
    try:
        return Comprehension(**doc.metadata)
    except ValidationError as e:
        raise ValueError(f"Invalid comprehension document {filepath}: {e}")
```

### Generating JSON Schema for Agent Prompting

```python
# Source: Pydantic documentation
from comprehension.schema import Comprehension, Observation
import json

def export_schemas():
    """Export JSON Schemas for LLM structured output."""
    schemas = {
        "comprehension": Comprehension.model_json_schema(),
        "observation": Observation.model_json_schema(),
    }

    for name, schema in schemas.items():
        with open(f"spec/schemas/{name}.json", "w") as f:
            json.dump(schema, f, indent=2)

    return schemas
```

### Validating Sample Documents

```python
# Source: pytest + Pydantic patterns
import pytest
from pathlib import Path
import frontmatter
from comprehension.schema import Comprehension, Observation

SAMPLE_DIR = Path("spec/examples")

@pytest.mark.parametrize("filepath", list(SAMPLE_DIR.glob("sample_comprehension*.md")))
def test_comprehension_samples_valid(filepath):
    """All sample comprehension documents must validate against schema."""
    doc = frontmatter.load(filepath)
    comp = Comprehension(**doc.metadata)  # Raises if invalid
    assert comp.posterior.confidence is not None
    assert len(comp.observations) > 0 or comp.prior.source != "accumulated"

@pytest.mark.parametrize("filepath", list(SAMPLE_DIR.glob("sample_observation*.md")))
def test_observation_samples_valid(filepath):
    """All sample observation documents must validate against schema."""
    doc = frontmatter.load(filepath)
    obs = Observation(**doc.metadata)
    assert obs.timestamp is not None
    assert obs.source is not None
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| README.md for all docs | AGENTS.md for AI-specific context | 2024-2025 | Machine-readable context separate from human docs |
| Ad-hoc context files | SKILL.md standard (progressive disclosure) | 2025 | Industry convergence on skill-based agent knowledge |
| Untyped AI outputs | Pydantic-validated structured outputs | 2024-2025 | Reliable extraction with automatic retry |
| XML for knowledge | Markdown + YAML frontmatter | 2023-2025 | Token efficiency, git-friendly, AI-preferred |

**Current innovations:**

- [AGENTS.md](https://agents.md/) - Open standard adopted by 60,000+ repositories; defines AI-specific project context
- [Agent Skills (SKILL.md)](https://developers.openai.com/codex/skills) - Anthropic-originated, adopted by Microsoft/OpenAI/GitHub; progressive disclosure for efficient context loading
- [Human Knowledge Markdown](https://github.com/digitalreplica/human-knowledge-markdown) - Knowledge graphs in Markdown+YAML frontmatter
- [Markform](https://github.com/jlevy/markform) - Structured forms in Markdown with JSON Schema export

**Deprecated/outdated:**
- XML-based knowledge representations (verbose, poor token efficiency)
- Untyped JSON blobs (no validation, prone to drift)
- Monolithic context files (one massive document causes context flooding)

## Open Questions

1. **Bayesian semantics precision**
   - What we know: Natural language confidence (high/medium/low) is the project requirement
   - What's unclear: Should there be a formal relationship between confidence levels? (e.g., "high = would bet 5:1")
   - Recommendation: Define operationally in spec document; keep simple for v1; formalize if needed in v2

2. **Observation linking strategy**
   - What we know: Comprehension references observations by ID
   - What's unclear: Should observations be embedded, linked, or both?
   - Recommendation: Link by ID in frontmatter; allow optional inline snippets in body; keeps documents modular

3. **Schema versioning strategy**
   - What we know: Documents need `spec` version field
   - What's unclear: Migration path when schema changes
   - Recommendation: Plan migration scripts from v1; use Pydantic v2 migration patterns; accept some manual migration for major changes

4. **Multi-document comprehension**
   - What we know: Some understanding spans multiple topics
   - What's unclear: How to represent cross-cutting comprehension
   - Recommendation: Allow `related` field linking to other comprehension IDs; treat as separate documents with explicit relationships

## Sources

### Primary (HIGH confidence)

- [Pydantic AI Documentation](https://ai.pydantic.dev/) - Structured output patterns, validation, schema generation
- [AGENTS.md Specification](https://agents.md/) - Open format for AI-focused project documentation; 60,000+ repos
- [Agent Skills Standard](https://developers.openai.com/codex/skills) - Progressive disclosure, SKILL.md format
- [python-frontmatter Documentation](https://python-frontmatter.readthedocs.io/) - Markdown+YAML parsing

### Secondary (MEDIUM confidence)

- [Human Knowledge Markdown](https://github.com/digitalreplica/human-knowledge-markdown) - Knowledge graphs in Markdown+YAML
- [Markform Specification](https://github.com/jlevy/markform) - Structured Markdown with JSON Schema export
- [JSON Schema Best Practices](https://json-schema.org/learn) - Schema design patterns
- [Policy Cards Research](https://arxiv.org/html/2510.24383v1) - Machine-readable governance formats

### Tertiary (LOW confidence - needs validation)

- [LLM-Prior Framework](https://arxiv.org/html/2508.03766v1) - Natural language to probability distribution; research-stage
- [CoBel-World Framework](https://arxiv.org/html/2509.21981) - Multi-agent belief collaboration; theoretical

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pydantic, PyYAML, python-frontmatter are mature, documented, production-used
- Architecture: MEDIUM-HIGH - Patterns derived from adjacent standards (AGENTS.md, SKILL.md); novel domain means some patterns need validation
- Pitfalls: MEDIUM - Derived from project research (PITFALLS.md) and general schema design experience; comprehension-specific pitfalls need discovery during implementation

**Research date:** 2026-02-13
**Valid until:** 60 days (stable domain; format design patterns don't change rapidly)
