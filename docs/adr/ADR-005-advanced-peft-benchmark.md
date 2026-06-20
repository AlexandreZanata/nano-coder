# ADR-005: Advanced PEFT and tensor-network benchmark expansion

**Status:** Accepted  
**Date:** 2026-06-20  
**Deciders:** Project owner

## Context

ADR-004 defined six baseline conditions (FewShot through MixedLanguages). New research input adds ten techniques spanning established PEFT (DoRA, GaLore), quantum-**inspired** tensor networks (MPO, QTHA, TTLoRA, TRG, iPEPS), randomized rank sketching, and one speculative regularizer (DecoherenceRegularization).

**Calibration:** Most concepts are **borrowed from established ML, differential geometry, information theory, and statistical mechanics** — not novel physics. The project's contribution is applying and measuring them on **small SLMs + JS/HTML/FreeMarker**, with honest evidence labeling.

Hardware constraint: **RTX 4060** — methods must be prioritized in waves.

## Decision

1. **Expand** the benchmark catalog per [TRAINING-METHODS.md](../TRAINING-METHODS.md).
2. **Split** training configuration into two axes:
   - `CompressionMethod` — how weights/gradients are constrained
   - `DataSchedule` — `MixedLanguages` | `IncrementalByLanguage` | `SingleLanguage`
3. **Adopt `BondDimension` (χ)** as the central hyperparameter for all tensor-network methods, with sweep {4, 8, 16, 32}.
4. **Label evidence** on every run: L1 Established | L2 QuantumInspired | L3 NovelApplication | L4 Speculative (BR-013).
5. **Execute in four waves** (W1–W4) — see TRAINING-METHODS.md — not all methods at once.
6. **Keep ADR-004 baselines** as Wave 1 anchors; DoRA added to Wave 1.

### Methods added

| Code name | Tier | Evidence |
|-----------|------|----------|
| `DoRA` | 1 | L1 |
| `GaLore` | 1 | L1 |
| `MPO` | 2 | L2 |
| `QTHA` | 2 | L2 |
| `TTLoRA` | 2 | L2 |
| `TRG` | 2 | L2 |
| `iPEPS` | 2 | L3 |
| `LowRankSketching` | 3 | L3 (meta-method → LoRA) |
| `DecoherenceRegularization` | 3 | L4 Speculative |

## Consequences

### Positive

- Richer benchmark narrative (χ vs language vs quality)
- Honest evidence taxonomy prevents overclaiming
- Wave rollout fits solo operator + 4060 VRAM
- TTLoRA/TRG prioritized for speed wins on iteration

### Negative

- Full matrix is combinatorially large — waves and matched-param comparisons required
- Some methods lack mature libraries for 0.5B coders — implementation risk
- iPEPS and DecoherenceRegularization may yield null results — budget accordingly

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Replace ADR-004 baselines entirely | Lose comparable anchor to standard LoRA/QLoRA |
| Run all methods × all χ × all languages at once | Exceeds 4060 time budget |
| Omit evidence labels | Violates honesty policy; weakens report |

## Supersedes

Extends [ADR-004](ADR-004-training-methods-benchmark.md) — does not replace baseline requirements.
