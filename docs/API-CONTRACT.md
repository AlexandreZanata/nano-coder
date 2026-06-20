# API Contract — nano-coder

> **Phase 1:** No public HTTP API. Pipeline is CLI-only.

---

## Current interface

All phase 1 operations are defined in **[PIPELINE-CONTRACT.md](PIPELINE-CONTRACT.md)**:

- CLI commands (`seeds import`, `generate dataset`, `train`, `benchmark`, `report export`)
- Config schema (`configs/pipeline.yaml`)
- Artifact formats (JSONL datasets, HF checkpoints, benchmark JSON)

---

## Future API (optional, not implemented)

If a web dashboard is added, it MUST:

| Requirement | Reference |
|-------------|-----------|
| Version prefix | `/v1/` on all routes |
| Auth | Bearer token + role from [ARCHITECTURE.md](ARCHITECTURE.md) RBAC |
| Errors | Same codes as PIPELINE-CONTRACT error table |
| Tenant | N/A for single-operator phase; add if multi-user |

### Planned resources (sketch)

```
GET  /v1/datasets
POST /v1/generation-runs
POST /v1/training-runs
POST /v1/benchmark-runs
GET  /v1/reports/{id}
```

**Do not implement** until use cases and OpenAPI spec are approved in a dedicated ADR.

---

## Agent note

Define OpenAPI before any HTTP handler code. Until then, refer agents to [PIPELINE-CONTRACT.md](PIPELINE-CONTRACT.md) only.
