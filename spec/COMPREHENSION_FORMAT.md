# Comprehension Format Specification

**Version:** comprehension/v1
**Status:** Active
**Last Updated:** 2026-02-13

## Overview

Comprehension documents represent **structured understanding**—not raw events, not code, but verified beliefs about how something works. They are the primary artifact in the comprehension-as-code system.

Key distinction:
- **Observations** = What happened (raw events)
- **Comprehension** = What we now believe (structured understanding)

Comprehension follows a Bayesian structure: prior belief → observations → posterior belief.

**Key insight:** The posterior IS the compression. No separate compression step is needed. The belief state encodes what all observations taught—we store the understanding, not the evidence.

## Document Structure

Comprehension documents use **Markdown with YAML frontmatter**:

```markdown
---
# YAML frontmatter with structured data
spec: comprehension/v1
id: comp-api-auth-001
# ... other fields
---

# Human-readable Markdown body
Summary, evidence, implications...
```

## Required Fields

### Identity

| Field | Type | Description |
|-------|------|-------------|
| `spec` | string | Schema version: `"comprehension/v1"` |
| `id` | string | Unique identifier (format: `comp-{domain}-{sequence}`) |
| `topic` | string | Natural language: what this comprehension is about |
| `domain` | string | Category for retrieval: `api`, `database`, `architecture`, etc. |

### Bayesian Structure

| Field | Type | Description |
|-------|------|-------------|
| `prior` | BeliefPrior | What was believed BEFORE observations |
| `observations` | List[string] | Observation IDs that informed this comprehension |
| `posterior` | BeliefPosterior | What is believed AFTER observations |

### Metadata

| Field | Type | Description |
|-------|------|-------------|
| `created` | datetime | ISO timestamp when first created |
| `updated` | datetime | ISO timestamp when last updated |
| `version` | integer | Increments on each update (default: 1) |
| `verified` | boolean | Has behavioral verification passed? (default: false) |

## BeliefPrior Object

Prior beliefs represent what was believed **before** seeing new evidence.

```yaml
prior:
  statement: "The authentication API uses REST endpoints"
  confidence: medium
  source: documentation
  reasoning: "Based on API docs from project setup"
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `statement` | string | Yes | Natural language belief |
| `confidence` | ConfidenceLevel | Yes | How confident before observations |
| `source` | string | Yes | Where prior came from |
| `reasoning` | string | No | Why this was believed |

### Source Values

- `training` — From LLM training data
- `accumulated` — From prior comprehension documents
- `documentation` — From project/API documentation
- `assumption` — Reasonable assumption without evidence
- `user` — Explicitly stated by user

## BeliefPosterior Object

Posterior beliefs represent updated understanding **after** incorporating evidence.

```yaml
posterior:
  statement: "The authentication API uses GraphQL, not REST"
  confidence: high
  update_reasoning: "REST 404 + GraphQL success confirms migration"
  observations_used:
    - obs-001
    - obs-002
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `statement` | string | Yes | Updated belief |
| `confidence` | ConfidenceLevel | Yes | Confidence after observations |
| `update_reasoning` | string | Yes | How observations changed belief |
| `observations_used` | List[string] | Yes | Observation IDs used in update |

## Confidence Levels

Confidence uses **natural language levels**, not numeric probabilities.

| Level | Value | Operational Definition |
|-------|-------|------------------------|
| HIGH | `high` | Verified against actual behavior; multiple independent confirmations; would bet on it |
| MEDIUM | `medium` | Single confirmation; reasonable evidence; plausible but not certain |
| LOW | `low` | Tentative hypothesis; needs validation before acting on it |
| UNKNOWN | `unknown` | Explicitly uncertain; do not act on without more evidence |

### Confidence Guidelines

- **HIGH** should require behavioral verification (not just reading docs)
- **MEDIUM** is appropriate for single-source information
- **LOW** signals "investigate before relying on this"
- **UNKNOWN** is better than false confidence

## Markdown Body

The body provides human-readable context. Recommended sections:

```markdown
# {Topic}

## Summary
One paragraph explaining the comprehension.

## Evidence
Bullet points referencing observations and what they showed.

## Implications
What this understanding means for future work.

## Related
Links to related comprehension documents.
```

## Example Document

```yaml
---
spec: comprehension/v1
type: comprehension
id: comp-api-auth-001
topic: Authentication API endpoint location
domain: api-integration

prior:
  statement: "The authentication API uses REST endpoints at /api/auth/*"
  confidence: medium
  source: documentation
  reasoning: "Based on initial API documentation"

observations:
  - obs-001
  - obs-002

posterior:
  statement: "The authentication API has migrated to GraphQL"
  confidence: high
  update_reasoning: "REST endpoint 404 + GraphQL mutation success confirms migration"
  observations_used:
    - obs-001
    - obs-002

created: 2026-02-13T10:30:00Z
updated: 2026-02-13T14:15:00Z
version: 2
verified: true
---

# Authentication API Location

## Summary

The authentication API has **migrated from REST to GraphQL**. Original REST endpoints no longer exist.

## Evidence

1. REST POST to `/api/auth/login` returned 404 (obs-001)
2. GraphQL mutation `authenticate` succeeded (obs-002)

## Implications

- All authentication calls must use GraphQL client
- Project documentation needs updating
- Other REST assumptions should be verified

## Related

- [API Base URL Configuration](./comp-api-base-001.md)
```

## Validation

Documents must validate against the Pydantic schema:

```python
from comprehension.schema import Comprehension

comp = Comprehension(**frontmatter_data)  # Raises ValidationError if invalid
```

## Versioning

- `spec` field tracks schema version
- `version` field tracks document version
- When schema changes, migration scripts update old documents

## Future: Emergence

As comprehensions accumulate, convergence detection (Phase 4) will ask "what does this remind me of?" When the same structure appears across domains with high confidence, it crystallizes into **meta-comprehension**—a pattern between patterns.

This is the **rising tide** approach: we don't force abstraction. Patterns become obvious through accumulation.
