# ADR-002: Student model selection strategy

**Status:** Proposed  
**Date:** 2026-06-20  
**Deciders:** Project owner

## Context

Goal: find the **smallest** SLM that learns JS/HTML/FreeMarker patterns via synthetic distillation. Hardware favors sub-1B–3B models. Research shows sharp quality drop below ~1B on complex tasks — we treat that as a benchmark outcome, not a blocker.

## Decision

1. **Start with** `Qwen2.5-Coder-0.5B` as first candidate (strong coding prior at smallest tier).
2. **Smoke test gate:** 200-example LoRA, 20 held-out tasks per language, Pass@1 ≥ 60%.
3. **Escalation order if smoke fails:**
   - Qwen2.5-Coder-1.5B
   - Gemma3-1B
   - Gemma3-270M documented as lower bound experiment only
4. **SmolLM3** evaluated if public weights fit same VRAM budget as Qwen 0.5B.

Final acceptance requires full benchmark (UC-004), not smoke alone.

## Consequences

### Positive

- Smallest-first aligns with project thesis (cost–benefit at minimum size)
- Documented escalation path produces valid negative results

### Negative

- 0.5B may fail early — extra iteration time
- Multiple downloads and HF dependency

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Start at 3B only | Does not answer "how small can we go?" |
| Train from scratch | Infeasible for solo operator budget |
| Single multilingual mega-model | Confounds language comparison |
