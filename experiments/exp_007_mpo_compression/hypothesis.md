# Hypothesis — EXP 007

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** QuantumInspired

## What I expect to happen
MPO at χ=16 reduces trainable params by ≥30% vs LoRA-r=16 with ≤2% Pass@1 drop.

## Why I expect this
Matrix product operators compress attention/MLP maps aggressively in recent LLM compression work.

## What would prove me wrong
Pass@1 drop above 5% or param reduction below 15%.

## Metrics I will measure
- [ ] Trainable params
- [ ] Pass@1
- [ ] Peak VRAM
- [ ] Inference tokens/s
