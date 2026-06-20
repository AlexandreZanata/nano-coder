# Hypothesis — EXP 012

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** NovelApplication

## What I expect to happen
Multi-pass DataReupload schedule improves Pass@1 by ≥3 pp vs single-pass LoRA at matched total token budget.

## Why I expect this
quantun-ia exp_008: reupload beat basic QNN by +5.6 pp (Holm p=0.012); depth via re-injection.

## What would prove me wrong
Single-pass LoRA wins on all languages or matched-token budget not honored.

## Metrics I will measure
- [ ] Pass@1 per language
- [ ] reuploadPasses
- [ ] Total tokens seen
