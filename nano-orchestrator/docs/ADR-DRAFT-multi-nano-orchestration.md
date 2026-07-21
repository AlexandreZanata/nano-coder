# ADR-DRAFT: Multi-nano orchestration (Orchestrator–Workers–Judge)

**Status:** Draft (in `nano-orchestrator/docs/` until promoted to `docs/adr/`)  
**Date:** 2026-07-21  
**Related:** ADR-002 student model selection, UC-004 evaluation

## Context

Solo sub-1B coding models are fast but brittle on multi-language requests. Hardware is limited to 8 GB VRAM. We want typed micro-task orchestration without paid APIs.

## Decision (proposed)

1. Use Orchestrator (~3B) → specialized Workers (&lt;1B) → Judge (sandbox-first).  
2. Cap workers at 5; unload orchestrator between decompose and merge.  
3. Human gate before persistence.  
4. Kill criterion: if orchestration loses to solo Qwen2.5-Coder-0.5B on gold set, stop.

## Consequences

- Extra operational complexity vs single model  
- Clear negative-result path (research value)  
- Aligns Application-layer AI rules (AGENT-CORE-PRINCIPLES)

## Promotion

When stable, copy to `docs/adr/ADR-00N-multi-nano-orchestration.md` and link from `docs/README.md`.
