# Hypothesis — EXP 011

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** NovelApplication

## What I expect to happen
GV-ALR on LoRA adapters reduces wall-clock training time by ≥25% vs fixed Adam at ≤1 pp Pass@1 drop.

## Why I expect this
quantun-ia exp_054/075 accepted: same AUC/PR-AUC with 58% wall-time and 5/8 epochs on RTX 4060.

## What would prove me wrong
No time savings or Pass@1 drop >2 pp vs fixed LR LoRA baseline (exp_001).

## Metrics I will measure
- [ ] Pass@1
- [ ] Wall-clock seconds
- [ ] Epochs to convergence
- [ ] Peak VRAM
