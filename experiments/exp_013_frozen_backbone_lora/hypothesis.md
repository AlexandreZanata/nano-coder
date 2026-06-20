# Hypothesis — EXP 013

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** NovelApplication

## What I expect to happen
LoRA on head + last 2 blocks only stays within 2 pp of full-layer LoRA with ≥20% VRAM savings.

## Why I expect this
quantun-ia exp_037/051/062/071: hybrid head accepted on all 4 domain anchors with ~289 trainable params.

## What would prove me wrong
Pass@1 drop >2 pp or VRAM savings <15% vs exp_001 full LoRA.

## Metrics I will measure
- [ ] Pass@1
- [ ] Trainable params
- [ ] Peak VRAM
- [ ] Frozen layer count
