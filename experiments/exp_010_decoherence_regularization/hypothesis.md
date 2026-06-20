# Hypothesis — EXP 010

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** Speculative

## What I expect to happen
Decoherence penalty (λ=0.1) reduces overfit on synthetic data — Pass@1 held-out +2% vs LoRA alone.

## Why I expect this
Speculative borrow from QM: penalize rising activation entropy during fine-tune.

## What would prove me wrong
No change or degradation — null result is valid and must be reported honestly as L4.

## Metrics I will measure
- [ ] Pass@1
- [ ] DecoherenceScore trajectory
- [ ] λ sensitivity
