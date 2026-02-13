# Observation Format Specification

**Version:** observation/v1
**Status:** Active
**Last Updated:** 2026-02-13

## Overview

Observation documents capture **raw events**—what happened, when, and where. They are inputs to comprehension, not conclusions.

Key distinction:
- **Observations** = What happened (events, without interpretation)
- **Comprehension** = What we now believe (structured understanding)

Observations are **episodic memory**: timestamped events that inform comprehension via Bayesian update. Once an observation has informed a belief, the observation itself can be garbage collected—the posterior IS the compression. We store beliefs, not evidence.

## Document Structure

Observation documents use **Markdown with YAML frontmatter**:

```markdown
---
# YAML frontmatter with event data
spec: observation/v1
id: obs-001
timestamp: 2026-02-13T10:25:00Z
# ... other fields
---

# Brief description of observation
Raw details, logs, or context...
```

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `spec` | string | Schema version: `"observation/v1"` |
| `id` | string | Unique identifier (format: `obs-{sequence}` or `obs-{timestamp-hash}`) |
| `timestamp` | datetime | ISO timestamp when observation was made |
| `source` | string | Agent/system that made the observation |
| `event` | string | Natural language description of what was observed |

## Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `context` | object | Additional context (project, task, prior beliefs, etc.) |
| `trace_ref` | string | Reference to full execution trace if available |

### Context Object

The `context` field captures additional metadata:

```yaml
context:
  project: example-project
  task: authenticate-user
  prior_belief: comp-api-auth-001/v1
  expected: 200
  actual: 404
```

Common context fields:
- `project` — Project identifier
- `task` — What the agent was trying to do
- `prior_belief` — Comprehension ID that set expectations
- `expected` / `actual` — For verification observations

## Markdown Body

The body provides human-readable details. Keep it brief—observations are raw data, not analysis.

```markdown
# Observation: {Brief title}

{One paragraph describing what was observed}

## Raw Data (optional)

{Logs, response bodies, error messages}
```

## Example Document

```yaml
---
spec: observation/v1
type: observation
id: obs-001
timestamp: 2026-02-13T10:25:00Z
source: agent/api-integration-agent
event: "HTTP POST to /api/auth/login returned 404 Not Found"
context:
  project: example-project
  task: authenticate-user
  expected: 200
trace_ref: trace-2026-02-13-abc123
---

# Observation: REST auth endpoint not found

Agent attempted POST to `/api/auth/login` with valid credentials and received HTTP 404.

## Raw Response

```
HTTP/1.1 404 Not Found
Content-Type: application/json

{"error": "Not Found"}
```
```

## Relationship to Comprehension

Observations are **referenced by ID** in comprehension documents:

```yaml
# In a comprehension document
observations:
  - obs-001
  - obs-002

posterior:
  observations_used:
    - obs-001
    - obs-002
```

Observations are inputs; comprehension is output.

## Validation

Documents must validate against the Pydantic schema:

```python
from comprehension.schema import Observation

obs = Observation(**frontmatter_data)  # Raises ValidationError if invalid
```

## Guidelines

1. **Be specific**: "POST /api/auth returned 404" not "auth failed"
2. **Include timestamps**: Essential for sequencing and debugging
3. **Reference traces**: Link to full logs when available
4. **Don't interpret**: Save conclusions for comprehension documents
5. **Keep bodies brief**: Raw data, not analysis

## Retention

Observations are ephemeral by design. Once an observation has informed a comprehension (via Bayesian update), it can be garbage collected. The comprehension's provenance field retains references to observation IDs, but the observation content itself is no longer needed.

**Key insight:** The posterior IS the compression. We don't need to store the evidence that produced a belief—we store the belief.

Retention policy details are implemented in Phase 2 (Bayesian Update) and Phase 3 (Belief Store).
