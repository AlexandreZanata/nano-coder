# Hypothesis — EXP 002

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** Established

## What I expect to happen
QLoRA achieves within 2% Pass@1 of LoRA at ≥20% lower peak VRAM on RTX 4060.

## Why I expect this
4-bit base weights are the standard VRAM-friendly baseline for solo GPU setups.

## What would prove me wrong
VRAM savings below 10% or Pass@1 drop above 5% vs LoRA at same dataset version.

## Metrics I will measure
- [ ] Pass@1
- [ ] Peak VRAM
- [ ] Model size on disk
