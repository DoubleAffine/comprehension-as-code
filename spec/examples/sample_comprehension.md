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
  reasoning: "Based on initial API documentation provided during project setup"

observations:
  - obs-001
  - obs-002

posterior:
  statement: "The authentication API has migrated to GraphQL; REST endpoints no longer exist"
  confidence: high
  update_reasoning: "REST endpoint failure (404) combined with successful GraphQL mutation confirms migration. Documentation is outdated."
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

The authentication API has **migrated from REST to GraphQL**. The original REST endpoints at `/api/auth/*` no longer exist.

## Evidence

1. REST POST to `/api/auth/login` returned 404 (obs-001)
2. GraphQL mutation `authenticate` succeeded with same credentials (obs-002)

## Implications

- All authentication calls must use GraphQL client
- Project documentation needs updating
- Other REST API assumptions should be verified

## Related

- This comprehension supersedes any prior beliefs about REST auth endpoints
