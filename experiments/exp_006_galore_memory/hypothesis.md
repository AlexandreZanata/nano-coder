# Hypothesis — EXP 006

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** Established

## What I expect to happen
GaLore peak VRAM stays within 120% of LoRA while updating full weights on 0.5B model.

## Why I expect this
Gradient low-rank projection targets full fine-tune expressivity at adapter-like memory.

## What would prove me wrong
OOM on 4060 at ci/smoke profile, or Pass@1 below LoRA by >5%.

## Metrics I will measure
- [ ] Peak VRAM
- [ ] Pass@1
- [ ] Trainable params (full vs adapter)
