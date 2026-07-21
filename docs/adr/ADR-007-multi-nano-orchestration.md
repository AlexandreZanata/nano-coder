# ADR-007: Multi-nano orchestration (Orchestrator–Workers–Judge)

**Status:** Accepted (negative outcome on quality gate)  
**Date:** 2026-07-21  
**Deciders:** Project owner  
**Related:** ADR-002 student model selection, UC-004 evaluation,  
[`nano-orchestrator/docs/NEGATIVE-RESULT.md`](../../nano-orchestrator/docs/NEGATIVE-RESULT.md)

## Context

Solo sub-1B coding models are fast but brittle on multi-language requests. Hardware is limited to 8 GB VRAM (RTX 4060 laptop). We wanted typed micro-task orchestration without paid APIs, specialized in JavaScript / HTML / FreeMarker.

## Decision

1. Use **Orchestrator (~3B) → specialized Workers (&lt;1B) → Judge (sandbox-first)**.  
2. Cap concurrent workers at **5** (ASI08); unload orchestrator between decompose and merge.  
3. **Human gate** before persistence (`auto_persist: false`; write only under `out/proposal/`).  
4. **Kill criterion:** if orchestration Pass@1 loses to solo `Qwen2.5-Coder-0.5B` on the frozen gold set, stop stacking features and keep the solo baseline.

## Outcome (measured 2026-07-21)

| Gate | Result |
|------|--------|
| GATE-001 orch Pass@1 ≥ solo | **FAIL** — 0.733 &lt; 0.867 |
| GATE-002 peak VRAM ≤ 6000 MB | **PASS** — 1577 MB |
| GATE-003 p50 ≤ 2000 ms | **PASS** — 323 ms |

**Product decision:** **keep solo `Qwen2.5-Coder-0.5B`** as the default coding worker for gold-set micro-tasks. The nano-orchestrator remains a research / instrumentation artifact, not the quality default.

## Consequences

### Positive

- Clear negative-result path (research value preserved)  
- Sandboxes, gold set, and bake-off tooling reusable for future worker experiments  
- Aligns Application-layer AI rules (AGENT-CORE-PRINCIPLES)

### Negative

- Orchestration did not beat solo on Pass@1 (JS fine-tune smoke regressed hard)  
- Extra operational complexity vs single model is unjustified for MVP quality

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Always ship orchestration | Failed GATE-001 kill criterion |
| Debate-by-default | ~2.5× cost; ASI08 risk; quality gate already failed |
| Ignore VRAM unload | Would exceed 8 GB budget under dual residency |

## References

- Spec: [`nano-orchestrator/README.md`](../../nano-orchestrator/README.md)  
- Draft (historical): [`nano-orchestrator/docs/ADR-DRAFT-multi-nano-orchestration.md`](../../nano-orchestrator/docs/ADR-DRAFT-multi-nano-orchestration.md)  
- Gate run: `nano-orchestrator/benchmarks/runs/success_gates.json`
