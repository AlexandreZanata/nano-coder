# ADR-004: Training methods benchmark matrix

**Status:** Accepted  
**Date:** 2026-06-20  
**Deciders:** Project owner

## Context

Core research question: which fine-tuning technique gives best cost–benefit per language for tiny models?

## Decision

Compare six conditions on the same published `DatasetVersion` (when possible):

| ID | TrainingMethod | Purpose |
|----|----------------|---------|
| A | `FewShot` | Baseline — no weight update |
| B | `FullFineTune` | Upper bound if VRAM allows |
| C | `LoRA` | Primary expected winner |
| D | `QLoRA` | VRAM-constrained hardware |
| E | `IncrementalByLanguage` | JS → HTML → FreeMarker sequential |
| F | `MixedLanguages` | All languages in one run |

Skip `FullFineTune` for a model if OOM — document as N/A, not failure.

**Extended by [ADR-005](ADR-005-advanced-peft-benchmark.md):** advanced `CompressionMethod` catalog in [TRAINING-METHODS.md](../TRAINING-METHODS.md). Baselines above remain Wave 1 anchors.

## Consequences

### Positive

- Directly answers project thesis
- Cost metrics captured per run (TrainingRunCompleted payload)

### Negative

- Multiplies GPU time (6× training runs)
- Incremental vs mixed confound if dataset sizes differ — use same total example count

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| LoRA only | No baseline comparison |
| Full FT only | Excludes most solo GPU setups |
