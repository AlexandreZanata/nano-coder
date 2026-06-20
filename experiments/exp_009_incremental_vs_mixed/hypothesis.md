# Hypothesis — EXP 009

**Date:** 2026-06-20
**Author:** pipeline-operator
**Evidence level:** Established

## What I expect to happen
IncrementalByLanguage training beats MixedLanguages Pass@1 on FreeMarker for 0.5B by ≥4%.

## Why I expect this
Small models may suffer interference when languages are shuffled; sequential specialization may help.

## What would prove me wrong
MixedLanguages wins on all languages — incremental provides no benefit.

## Metrics I will measure
- [ ] Pass@1 per language
- [ ] DataSchedule tag
- [ ] Total training time
