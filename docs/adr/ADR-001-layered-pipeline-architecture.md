# ADR-001: Layered pipeline architecture for nano-coder

**Status:** Accepted  
**Date:** 2026-06-20  
**Deciders:** Project owner

## Context

nano-coder is a research pipeline (synthetic data → train SLM → benchmark), not a CRUD web app. We need structure that supports testable domain rules, swappable LLM/GPU infrastructure, and agent-assisted development without anemic scripts.

## Decision

Adopt **layered DDD** as defined in [ARCHITECTURE.md](../ARCHITECTURE.md):

- **Domain:** rules, state machines, events (no HF/API imports)
- **Application:** use cases UC-001–UC-005
- **Infrastructure:** teacher API, HuggingFace, parsers, sandbox
- **Interfaces:** CLI (`nano-coder`)

Phase 1 has **CLI only** — no HTTP API until ADR for dashboard exists.

## Consequences

### Positive

- Business rules (BR-001–BR-012) testable without GPU
- Clear boundaries for agent edits (Application orchestrates, Domain decides)
- Aligns with Agent Harness AGENT-CORE-PRINCIPLES

### Negative

- More boilerplate than a single Jupyter notebook
- Requires discipline to keep Domain pure

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Single notebook pipeline | Hard to test rules; poor incremental verification |
| Microservices | Overkill for solo operator |
| REST-first API | No remote consumers in phase 1 |
