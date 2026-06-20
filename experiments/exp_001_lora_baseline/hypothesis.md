# Hypothesis — EXP 001

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** Established

## What I expect to happen
LoRA rank 16 reaches Pass@1 ≥ 60% on smoke held-out for all three TargetLanguage values.

## Why I expect this
LoRA is the established PEFT anchor; all advanced methods compare against it at matched rank or param budget.

## What would prove me wrong
Pass@1 below 50% on any language after smoke profile, or peak VRAM above 7 GB on 0.5B QLoRA-class budget.

## Metrics I will measure
- [ ] Pass@1
- [ ] Pass@5
- [ ] Peak VRAM
- [ ] Trainable params
- [ ] Wall-clock time
