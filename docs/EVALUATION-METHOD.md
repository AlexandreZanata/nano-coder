# Evaluation Method — nano-coder

> Defines metrics, held-out protocol, and comparability rules for `BenchmarkRun`.

---

## Held-out test set

| Property | Value |
|----------|-------|
| Version | `held-out-v1` (immutable once created) |
| Size target | 50–100 tasks per `TargetLanguage` |
| Source | Manual + held-back from seed authoring (never in training) |
| Isolation | BR-004 enforced in CI and pre-benchmark checks |

Task format matches training: `instruction` → expected properties (not necessarily exact string match).

---

## Correctness checks (per language)

| Language | Automated checks |
|----------|------------------|
| `JavaScript` | Parse (e.g. acorn/esbuild), ESLint ruleset, optional Node sandbox run |
| `HTML` | HTML5 parser, optional accessibility subset |
| `FreeMarker` | Template syntax validator, render with fixture data where applicable |

A task **passes** when all configured checks for that task type succeed.

---

## Primary metrics

### Pass@k

```
Pass@k = P(at least 1 of k samples passes | task)
```

Report **Pass@1** and **Pass@5** per language and aggregated.

### Syntax validity rate

Fraction of generated samples that pass parser/lint regardless of task match (diagnostic for collapse).

### Training cost

| Metric | Unit |
|--------|------|
| Wall-clock training time | seconds |
| Peak VRAM | GB |
| Total GPU-hours | hours |

### Inference cost

| Metric | Unit |
|--------|------|
| Mean latency | ms/token |
| Throughput | tokens/s |
| Model size on disk | MB (including quantized export) |

### LLM-as-judge (secondary)

`TeacherModel` scores 1–5 on correctness and style on a **fixed 10% sample** of benchmark outputs.

Judge scores are **not** sole pass criteria — automated checks prevail (BR-010).

---

## Comparison matrix (final report)

| Dimension | Values |
|-----------|--------|
| Rows | `CompressionMethod` + `EvidenceLevel` + χ or rank |
| Columns | `TargetLanguage` × metric |
| Required footnotes | `DataSchedule`, `DatasetVersion`, checkpoint, test set |

See full template: [TRAINING-METHODS.md](TRAINING-METHODS.md) § Comparison table.

Example (Wave 1–2 subset):

| Method | Evidence | χ/r | JS Pass@1 | HTML Pass@1 | FMT Pass@1 | Peak VRAM (GB) | Train (min) |
|--------|----------|-----|-----------|-------------|------------|----------------|-------------|
| FewShot | L1 | — | … | … | … | 0 | 0 |
| LoRA | L1 | r=16 | … | … | … | … | … |
| DoRA | L1 | r=16 | … | … | … | … | … |
| TTLoRA | L2 | χ=16 | … | … | … | … | … |
| TRG | L2 | χ=16 | … | … | … | … | … |

### Bond dimension heatmap (required for tensor methods)

Report **χ × TargetLanguage × Pass@1** for `MPO`, `QTHA`, `TTLoRA`, `TRG`, `iPEPS`.

---

## Smoke test (Phase 2 gate)

Before full benchmark:

- 20 held-out tasks per language
- **Pass@1 ≥ 60%** after minimal LoRA (200 examples, 1 epoch) → proceed with candidate
- Else try next larger `StudentModel` or document failure

---

## Negative result documentation

If sub-1B models fail complex tasks:

- Report at which task complexity (tag buckets) failure begins
- Compare whether `IncrementalByLanguage` outperforms `MixedLanguages`
- Recommend minimum viable model size per language

These outcomes satisfy project success criteria — the benchmark is the product.

---

## Test pyramid (implementation)

```
E2E (5%)       → full CLI: seeds → generate → train → benchmark
Integration (20%) → use cases + real parsers, mocked LLM
Unit (75%)     → domain rules, state machines, quality gate logic
```

Domain coverage target: **≥ 90%** on rules and state transitions.
