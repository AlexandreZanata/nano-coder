# ADR-006: Adopt quantun-ia top-3 proven methods as transfer research

**Status:** Accepted  
**Date:** 2026-06-20  
**Deciders:** Project owner

## Context

quantun-ia ran 80+ hypothesis-first experiments with MicroQML Bench on RTX 4060. Most quantum recipes failed or were inconclusive (`docs/negative_results.md` in quantun-ia). Three methods showed the **strongest, most replicable success** and are transferable as **research hypotheses** to nano-coder's SLM fine-tuning benchmark.

## Decision

Adopt as **Tier Q** compression/optimization methods (see [QUANTUN-IA-PROVEN-METHODS.md](../QUANTUN-IA-PROVEN-METHODS.md)):

| Rank | Method | quantun-ia key experiments |
|------|--------|---------------------------|
| 1 | `GradientVarianceAdaptiveLR` | exp_015, exp_054, exp_075 |
| 2 | `DataReupload` | exp_008, exp_001, exp_002 |
| 3 | `FrozenBackboneHybridHead` | exp_037, exp_051, exp_062, exp_071 |

Register Wave Q experiments exp_011–exp_013 after Wave 1 LoRA anchor.

Label evidence as **L3 NovelApplication** for code SLMs until local replication — quantun-ia wins are cited as prior art, not guaranteed transfer.

## Consequences

### Positive

- Research agenda grounded in empirical wins, not only literature speculation
- GV-ALR complements existing `GaLore` entry in Tier 1
- FrozenBackboneHybridHead aligns with partial LoRA — low VRAM on 4060
- Honest negative transfer still valid outcome

### Negative

- QML ≠ code generation — transfer may fail
- GV-ALR adds optimizer complexity to training stack
- DataReupload increases token budget — must match controls

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Import all quantun-ia quantum recipes | exp_068: most recipes 0 domain wins |
| Skip quantun-ia linkage | User requested proven methods alongside tensor methods |
| Promote entanglement / warm-start | Rejected in quantun-ia negative_results |

## Supersedes

Extends [ADR-005](ADR-005-advanced-peft-benchmark.md) — adds Tier Q, does not replace tensor methods.
