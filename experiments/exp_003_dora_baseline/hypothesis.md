# Hypothesis — EXP 003

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** Established

## What I expect to happen
DoRA at rank 16 outperforms LoRA-r=16 on HTML and FreeMarker Pass@1 by ≥3% at matched param count.

## Why I expect this
Magnitude-direction decomposition improves convergence on structured template outputs.

## What would prove me wrong
DoRA worse than LoRA on all languages, or param count differs by more than 10% without footnote.

## Metrics I will measure
- [ ] Pass@1 per language
- [ ] Trainable params
- [ ] Convergence step
