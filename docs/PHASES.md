# Experiment Phases — nano-coder

> Sequential phases for the SLM distillation benchmark. See [PHASES.md](PHASES.md) for detail.

---

## Phase overview

```
Phase 1: Synthetic Data Generation     → DatasetGenerationRun, SyntheticDataset
Phase 2: Student Model Selection       → viability smoke test, ADR-002
Phase 3: Training Method Comparison    → TrainingRun × TrainingMethod
Phase 4: Evaluation                      → BenchmarkRun, Pass@k, cost metrics
Phase 5: Reporting                     → comparative tables, final report
```

---

## Phase 1 — Synthetic data generation

**Goal:** Build ~1,500–3,000 validated examples per `TargetLanguage` (~5–9k total).

| Step | Action |
|------|--------|
| 1 | Author 50–100 `GoldSeedExample` per language (manual, high quality) |
| 2 | Expand via Self-Instruct / Evol-Instruct using `TeacherModel` |
| 3 | Apply `QualityGate` pipeline (syntax, lint, optional LLM-as-judge) |
| 4 | Manual review sample (≥5%) by `PipelineOperator` |
| 5 | Publish `SyntheticDataset` with `DatasetVersion` |

**Budget:** ~$50–200 API/GPU; ~1 week for solo operator.

---

## Phase 2 — Student model selection

**Goal:** Pick the smallest `StudentModel` that learns basic patterns on a smoke subset.

| Candidate | Params | Notes |
|-----------|--------|-------|
| Qwen2.5-Coder | 0.5B / 1.5B | Strong coding baseline |
| Gemma 3 | 270M / 1B | Very small footprint |
| SmolLM3 | varies | Public engineering blueprint |

**Exit criteria:** Model produces syntactically valid output on ≥60% of smoke tasks after minimal LoRA on 200 examples.

---

## Phase 3 — Training method comparison

**Goal:** Compare `CompressionMethod` × `DataSchedule` under controlled `DatasetVersion`.

Full catalog: **[TRAINING-METHODS.md](TRAINING-METHODS.md)** · ADR: [ADR-004](adr/ADR-004-training-methods-benchmark.md), [ADR-005](adr/ADR-005-advanced-peft-benchmark.md), [ADR-006](adr/ADR-006-quantun-ia-proven-transfers.md)

### Wave rollout (RTX 4060)

| Wave | Methods | Priority |
|------|---------|----------|
| W1 | `FewShot`, `LoRA`, `QLoRA`, `DoRA` | Required — anchors |
| **WQ** | **`GradientVarianceAdaptiveLR`, `DataReupload`, `FrozenBackboneHybridHead`** | **Recommended — quantun-ia proven** |
| W2 | `GaLore`, `TTLoRA`, `TRG` | Required — tensor entry + speed |
| W3 | `MPO`, `QTHA`, `LowRankSketching→LoRA` | Recommended |
| W4 | `iPEPS`, `DecoherenceRegularization`, `IncrementalByLanguage`, `FullFineTune` | Optional / exploratory |

quantun-ia evidence: [QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md)

### Baselines (Tier 0)

| ID | CompressionMethod | Description |
|----|-------------------|-------------|
| T0-A | `FewShot` | No weight update |
| T0-B | `FullFineTune` | Full weights (if VRAM allows) |
| T0-C | `LoRA` | Standard low-rank adapters |
| T0-D | `QLoRA` | 4-bit base + LoRA |

### Advanced methods (summary)

| Tier | Methods | Evidence |
|------|---------|----------|
| 1 | `DoRA`, `GaLore` | Established (L1) |
| **Q** | **`GradientVarianceAdaptiveLR`, `DataReupload`, `FrozenBackboneHybridHead`** | **quantun-ia proven → L3 transfer** |
| 2 | `MPO`, `QTHA`, `TTLoRA`, `TRG`, `iPEPS` | Quantum-inspired / tensor (L2–L3) |
| 3 | `LowRankSketching`, `DecoherenceRegularization` | Novel application / speculative (L3–L4) |

**Bond dimension χ:** sweep {4, 8, 16, 32} for all tensor methods — see TRAINING-METHODS.md § Bond dimension.

---

## Phase 4 — Evaluation

**Goal:** Measure correctness, cost, and quality on `HeldOutTestSet`.

See [EVALUATION-METHOD.md](EVALUATION-METHOD.md) for metrics and acceptance criteria.

---

## Phase 5 — Reporting

**Goal:** Answer: *Which technique gives the best cost–benefit per language?*

Deliverables:

- Method × language × metric table
- VRAM / training time / inference tokens/s
- Qualitative LLM-as-judge scores
- Documented negative results (e.g. sub-1B limits on complex tasks)

---

## Research questions

1. How far can model size shrink before quality collapses per language?
2. Which `CompressionMethod` delays that collapse longest at matched param budget?
3. Is **`BondDimension` χ** more informative than raw LoRA rank for JS vs HTML vs FreeMarker?
4. Do tensor methods (`TTLoRA`, `TRG`, `MPO`) beat LoRA/DoRA on RTX 4060 time and VRAM?
5. Is `IncrementalByLanguage` better than `MixedLanguages` for the best method from Wave 1–2?
6. Does `DecoherenceRegularization` (L4 speculative) change collapse point — or null result?
7. Does synthetic-only data match manual gold on held-out tasks?

Negative findings are valid outcomes — document them in the final report.
