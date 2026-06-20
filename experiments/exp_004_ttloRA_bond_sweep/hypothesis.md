# Hypothesis — EXP 004

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** QuantumInspired

## What I expect to happen
TTLoRA at χ=16 matches LoRA-r=16 Pass@1 with fewer trainable parameters on JavaScript.

## Why I expect this
Tensor train (DMRG-style) factorization may allocate rank budget more efficiently across layers.

## What would prove me wrong
All χ values below LoRA Pass@1 by >5%, or VRAM higher than LoRA at matched params.

## Metrics I will measure
- [ ] Pass@1 vs χ
- [ ] Trainable params
- [ ] Peak VRAM
- [ ] χ × language heatmap
