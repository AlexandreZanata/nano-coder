# Hypothesis — EXP 005

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** QuantumInspired

## What I expect to happen
TRG fine-tuning completes in ≥30% less wall-clock time than LoRA at similar Pass@1 on mixed dataset.

## Why I expect this
Renormalization-group coarse-graining reported ~45-50% training time reduction in tensorized FT literature.

## What would prove me wrong
Speedup below 15% or Pass@1 drop above 3% vs LoRA.

## Metrics I will measure
- [ ] Wall-clock seconds
- [ ] Pass@1
- [ ] Peak VRAM
