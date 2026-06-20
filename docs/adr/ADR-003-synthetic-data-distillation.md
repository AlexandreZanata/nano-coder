# ADR-003: Synthetic data generation via teacher distillation

**Status:** Accepted  
**Date:** 2026-06-20  
**Deciders:** Project owner

## Context

Standard corpora (The Stack, StackOverflow) lack properties needed for small models to learn algorithmic planning (Phi-1 finding). Solo operator budget: ~$50–200, ~1 week. Target: ~1.5k–3k examples per language.

## Decision

Use **teacher–student distillation with synthetic data**:

1. **50–100 manual gold seeds** per `TargetLanguage` (non-negotiable quality anchor)
2. **Expand** via Self-Instruct / Evol-Instruct using `TeacherModel` (Claude/GPT class API)
3. **Filter** with automated gates + LLM-as-judge + 5% manual review
4. **No training data** from held-out test set (BR-004)

Expansion and judge may use the same teacher provider with different prompts.

## Consequences

### Positive

- Matches 2026 industry standard for domain-specific fine-tuning at small scale
- Reproducible with documented seeds and `DatasetVersion`
- Quality gates reduce garbage-in risk

### Negative

- API cost and vendor lock for generation phase
- Synthetic bias — must report gap vs manual gold on held-out
- FreeMarker validation tooling less mature than JS/HTML

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Scrape only | Poor planning signal; licensing noise |
| 100% manual 9k examples | Not feasible for solo timeline |
| No manual seeds | Quality collapse in small models |
