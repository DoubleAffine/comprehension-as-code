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
