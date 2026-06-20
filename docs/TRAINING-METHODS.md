# Training Methods — nano-coder

> Full catalog of fine-tuning techniques for Phase 3 benchmarks.
> **Honesty policy:** concepts borrowed from differential geometry, information theory, and statistical mechanics are labeled as such — not presented as novel physics.

**Related:** [GLOSSARY.md](GLOSSARY.md) · [EVALUATION-METHOD.md](EVALUATION-METHOD.md) · [ADR-004](adr/ADR-004-training-methods-benchmark.md) · [ADR-005](adr/ADR-005-advanced-peft-benchmark.md)

---

## Two orthogonal axes

Every `TrainingRun` is defined by **two independent choices**:

| Axis | Enum | Examples |
|------|------|----------|
| **CompressionMethod** | How weights/gradients are constrained | `LoRA`, `MPO`, `GaLore`, … |
| **DataSchedule** | How languages are presented | `MixedLanguages`, `IncrementalByLanguage`, `SingleLanguage` |

Example run tag: `MPO + MixedLanguages + bondChi=16`.

Baseline runs from ADR-004 remain valid. Advanced methods below extend the **CompressionMethod** axis.

---

## Evidence levels

| Level | Label | Meaning | Report requirement |
|-------|-------|---------|-------------------|
| L1 | `Established` | Mainstream ML; libraries available | Cite standard papers/libs |
| L2 | `QuantumInspired` | Classical simulation of quantum/tensor-network math; active research (ICML 2026 workshops) | Cite source paper; note "simulated, no quantum hardware" |
| L3 | `NovelApplication` | Known math applied to new context (small SLM + code) | Mark as under-explored for our domain |
| L4 | `Speculative` | No direct literature support; exploratory | Mark as hypothesis; negative results valid |

All benchmark rows **must** include `evidenceLevel` in artifacts (BR-013).

---

## Tier 0 — Baselines (ADR-004)

| ID | CompressionMethod | Evidence | Role |
|----|-------------------|----------|------|
| T0-A | `FewShot` | L1 | No weight update — inference baseline |
| T0-B | `FullFineTune` | L1 | Upper bound if VRAM allows (RTX 4060: often N/A at 1.5B+) |
| T0-C | `LoRA` | L1 | Standard low-rank adapters — primary comparison anchor |
| T0-D | `QLoRA` | L1 | 4-bit base + LoRA — VRAM-friendly baseline |

**DataSchedule variants:** run T0-C/D with both `MixedLanguages` and `IncrementalByLanguage`.

---

## Tier Q — quantun-ia proven methods (transfer research)

> Full evidence tables: **[QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md)**
> Source: [quantun-ia](https://github.com/AlexandreZanata/quantun-ia) MicroQML Bench — top 3 by cross-benchmark success on RTX 4060.
> **Status:** Hypotheses for SLM transfer — not yet validated on JS/HTML/FreeMarker.

| Rank | CompressionMethod | quantun-ia evidence | nano-coder Wave Q |
|------|-------------------|---------------------|-------------------|
| 1 | `GradientVarianceAdaptiveLR` | exp_054+075 accepted (58% train time, parity AUC); exp_015 Holm +7.8 pp | exp_011 |
| 2 | `DataReupload` | exp_008+001 Holm +5.6–7.6 pp vs basic QNN | exp_012 |
| 3 | `FrozenBackboneHybridHead` | exp_037/051/062/071 accepted 4/4 domain anchors | exp_013 |

### GradientVarianceAdaptiveLR (GV-ALR)

| Field | Value |
|-------|-------|
| **Origin** | quantun-ia `adaptive_lr.py` — variance-scaled Adam for barren-plateau escape |
| **Evidence** | L1 in quantun-ia; **L3 NovelApplication** for code SLM until exp_011 runs |
| **Hypothesis** | ≥25% wall-clock reduction vs fixed LR LoRA at ≤1 pp Pass@1 drop |
| **Pairs with** | LoRA, DoRA, TTLoRA (optimizer layer, not weight compression) |
| **Key hyperparams** | `varTarget`, `warmupEpochs`, `minScale`, `maxScale` |

### DataReupload

| Field | Value |
|-------|-------|
| **Origin** | Quantum re-upload circuits (exp_008) — multi-pass feature injection |
| **Evidence** | L2 QuantumInspired in quantun-ia; L3 for SLM multi-pass schedule |
| **Hypothesis** | ≥3 pp Pass@1 vs single-pass at matched token budget |
| **SLM mapping** | Re-present batch K times; re-inject embeddings between adapter blocks |
| **Key hyperparams** | `reuploadPasses`, `targetBlocks` (per language) |

### FrozenBackboneHybridHead

| Field | Value |
|-------|-------|
| **Origin** | quantun-ia freeze ~1.1M params, train ~289 hybrid head (4-domain replication) |
| **Evidence** | L2 in quantun-ia; maps directly to partial LoRA |
| **Hypothesis** | Within 2 pp of full-layer LoRA; ≥20% VRAM savings; ≥60% fewer trainable params |
| **SLM mapping** | Freeze Qwen 0.5B; LoRA on `lm_head` + last 2 blocks only |
| **Key hyperparams** | `frozenLayers`, `loraRank`, `trainableModulePattern` |

**Wave Q rollout (after Wave 1 LoRA anchor):** exp_011 → exp_012 → exp_013, then best Wave Q + best Wave 2 tensor method.

---

## Tier 1 — Established advanced PEFT (L1)

### DoRA — Decomposed Magnitude-Direction Adaptation

| Field | Value |
|-------|-------|
| **Code name** | `DoRA` |
| **Origin** | Vector geometry — decompose weight updates into magnitude and direction components |
| **Evidence** | L1 — mainstream 2026; available in standard PEFT libraries |
| **Hypothesis for nano-coder** | Better convergence on multi-step HTML/FreeMarker templates vs plain LoRA at same rank |
| **Key hyperparams** | `loraRank` (compare 8/16/32 against LoRA) |
| **VRAM (4060)** | Similar to LoRA |
| **Implementation note** | `peft` DoRA config; pair with `MixedLanguages` first |

### GaLore — Gradient Low-Rank Projection

| Field | Value |
|-------|-------|
| **Code name** | `GaLore` |
| **Origin** | Optimization dynamics — project **gradients** (not weights) into low-rank subspace during full fine-tune |
| **Evidence** | L1 — CoLoRAI / ICML 2026 workshop; distinct from LoRA architecturally |
| **Hypothesis** | Full fine-tune memory closer to LoRA while updating all weights — may help 0.5B on JS logic |
| **Key hyperparams** | `galoreRank`, update interval, target modules (attn + MLP) |
| **VRAM (4060)** | Higher than LoRA, lower than naive FullFineTune — monitor peak |
| **Implementation note** | Not a PEFT adapter — separate training loop integration |

---

## Tier 2 — Tensor networks & quantum-inspired (L2–L3)

> **Calibration:** These are **known mathematical frameworks** (tensor networks from many-body quantum physics, renormalization group from statistical mechanics) **applied** to neural weight compression. They are not new physics; applicability to sub-1B code models is the open question.

### MPO — Matrix Product Operators

| Field | Value |
|-------|-------|
| **Code name** | `MPO` |
| **Origin** | Many-body quantum physics — chain of low-dimensional matrix products replacing dense linear maps |
| **Evidence** | L2 — CompactifAI / recent LLM compression (e.g. ~70% param reduction, ~93% memory on LLaMA-2 7B with quantization, ~2× train speedup reported) |
| **Hypothesis** | More aggressive compression than LoRA on 4060; viable for 0.5B–1.5B coder models |
| **Key hyperparams** | **`BondDimension` (χ)** — central compression knob (see § Bond dimension sweep) |
| **VRAM (4060)** | Target method — designed for constrained GPU |
| **Implementation note** | Use existing MPO/tensor libraries where possible; document bond χ explicitly |

### QTHA — Quantum Tensor Hybrid Adaptation

| Field | Value |
|-------|-------|
| **Code name** | `QTHA` |
| **Origin** | Quantum-inspired — simulated superposition of states to exceed classical LoRA rank limits |
| **Evidence** | L2 — empirical train-loss improvements vs classical LoRA in literature; **runs on classical GPU** |
| **Hypothesis** | Better parameter efficiency when LoRA rank is capped low (χ ≤ 8) for tiny models |
| **Key hyperparams** | `bondDimension`, QTN depth, comparable param budget to LoRA-rank-16 |
| **VRAM (4060)** | Similar order to LoRA/MPO |
| **Implementation note** | Label outputs "quantum-**inspired**" in all reports — no quantum hardware |

### TTLoRA — Tensor Train Decomposition

| Field | Value |
|-------|-------|
| **Code name** | `TTLoRA` |
| **Origin** | Tensor Train (TT) — 1D chain decomposition from DMRG / quantum 1D systems |
| **Evidence** | L2 — TT-LoRA matches or beats other PEFT at smaller model sizes in reported benchmarks |
| **Hypothesis** | **Entry point** to tensor-network family — simpler than full MPO/iPEPS for first experiments |
| **Key hyperparams** | TT ranks per core, **`bondDimension` (χ)** |
| **VRAM (4060)** | Favorable — recommended first tensor method to implement |
| **Implementation note** | Compare directly against LoRA at matched trainable param count |

### TRG — Tensor Renormalization Group Fine-Tuning

| Field | Value |
|-------|-------|
| **Code name** | `TRG` |
| **Origin** | Statistical mechanics — coarse-graining across scales (RG) applied to weight tensor factorization |
| **Evidence** | L2 — reported ~45–50% training time reduction (e.g. 10–11 min vs 20 min) without accuracy loss in iPEPS-TRG fine-tuning experiments |
| **Hypothesis** | Faster iteration on 4060 — critical for solo operator running large method matrix |
| **Key hyperparams** | **`bondDimension` (χ)**, TRG truncation scheme, target layers (attn vs MLP) |
| **VRAM (4060)** | Compression + speed — high priority after TTLoRA |
| **Implementation note** | "Zoom-out" narrative is physics metaphor; metric is wall-clock time (BR-012 comparable runs) |

### iPEPS — Infinite Projected Entangled Pair States

| Field | Value |
|-------|-------|
| **Code name** | `iPEPS` |
| **Origin** | 2D tensor network from condensed-matter physics (2D entanglement structure) |
| **Evidence** | L3 — used in physics; **little evidence for small code SLMs** |
| **Hypothesis** | 2D correlation structure in attention maps may help HTML nesting / FreeMarker macro scope — **unexplored** |
| **Key hyperparams** | **`bondDimension` (χ)**, iPEPS site grid, TRG optimization steps |
| **VRAM (4060)** | Likely heavier than TT/MPO — run last in Tier 2 |
| **Implementation note** | Mark L3 in all reports; failure is a valid finding |

---

## Tier 3 — Advanced rank selection & experimental (L3–L4)

### LowRankSketching — Randomized Rank Estimation

| Field | Value |
|-------|-------|
| **Code name** | `LowRankSketching` |
| **Origin** | Randomized linear algebra — Johnson-Lindenstrauss projections to estimate minimal rank preserving layer information |
| **Evidence** | L3 — active frontier (CoLoRAI ICML 2026); not a standalone trainer — **meta-method** |
| **Hypothesis** | Replace arbitrary LoRA rank (8/16/32) with measured rank per layer before training |
| **Protocol** | 1) Sketch each target layer on N batch samples → estimated rank r*  2) Train LoRA/DoRA/TTLoRA with rank=r*  3) Compare vs fixed-rank baseline |
| **Key hyperparams** | sketch samples, failure probability ε, target layers |
| **VRAM (4060)** | One-time sketch pass + standard PEFT train |
| **Implementation note** | Report as `LowRankSketching → LoRA` composite method |

### DecoherenceRegularization — Activation Purity Metric (speculative)

| Field | Value |
|-------|-------|
| **Code name** | `DecoherenceRegularization` |
| **Origin** | **Speculative borrow** from quantum mechanics — decoherence as loss of state "purity" |
| **Evidence** | L4 — **no direct literature found**; project-native hypothesis |
| **Hypothesis** | Penalize rising activation entropy during fine-tune → regularization akin to physics-informed early stopping |
| **Metric (proposed)** | `DecoherenceScore` = entropy of hidden-state distribution vs baseline "pure" (low-entropy) reference |
| **Loss** | `L_total = L_task + λ · DecoherenceScore` |
| **Key hyperparams** | λ, measured layers, reference checkpoint |
| **VRAM (4060)** | Overhead from activation stats — keep λ sweep small |
| **Implementation note** | **Optional Tier 3 experiment** — document null result if quality unchanged |

---

## Bond dimension (χ) — central hyperparameter axis

| Field | Value |
|-------|-------|
| **Code name** | `BondDimension` |
| **Definition** | Compression knob χ from tensor-network literature — analogous to LoRA rank but with tensor-specific meaning (virtual bond size between cores) |
| **Not the same as** | `loraRank` — related role, different geometry; do not conflate in reports without mapping table |

### Sweep protocol (mandatory for tensor methods)

For each of `MPO`, `QTHA`, `TTLoRA`, `TRG`, `iPEPS`:

| χ value | Purpose |
|---------|---------|
| 4 | Aggressive compression — expect collapse on complex JS |
| 8 | Match LoRA-rank-8 param budget |
| 16 | Match LoRA-rank-16 param budget |
| 32 | Upper bound for 4060 experiments |

**Research framing:** relate χ to "how much entanglement/correlation capacity" the model needs per language:

- **JavaScript** — sequential logic, higher effective χ expected?
- **HTML** — nested 2D structure, test iPEPS/TRG advantage
- **FreeMarker** — macro scope + text interpolation, mixed structure

Report: **χ × language × Pass@1** heatmap, not just "rank 16 vs 32".

---

## Recommended benchmark rollout (RTX 4060)

Execute in waves to manage GPU time. Same `DatasetVersion` within each wave.

### Wave 1 — Anchors (required)

```
FewShot, LoRA, QLoRA, DoRA  ×  MixedLanguages  ×  loraRank/bondChi ∈ {8, 16}
```

### Wave 2 — Gradient & tensor entry (required)

```
GaLore, TTLoRA, TRG  ×  MixedLanguages  ×  bondChi ∈ {8, 16}
```

### Wave 3 — Aggressive compression (recommended)

```
MPO, QTHA  ×  MixedLanguages  ×  bondChi ∈ {4, 8, 16}
LowRankSketching → LoRA  ×  MixedLanguages
```

### Wave Q — quantun-ia proven transfers (recommended after Wave 1)

```
GV-ALR + LoRA              ×  MixedLanguages   (exp_011)
DataReupload + LoRA        ×  MixedLanguages   (exp_012)
FrozenBackbone + LoRA      ×  MixedLanguages   (exp_013)
```

Evidence: [QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md) · ADR-006

### Wave 4 — Exploratory (optional)

```
iPEPS  ×  bondChi ∈ {8, 16}
DecoherenceRegularization + LoRA  ×  λ ∈ {0.01, 0.1}
IncrementalByLanguage  ×  best method from Waves 1–2
FullFineTune  ×  if VRAM permits smoke model only
```

---

## Comparison table template (final report)

| Method | Evidence | χ / rank | JS Pass@1 | HTML Pass@1 | FMT Pass@1 | Peak VRAM | Train (min) | Trainable params |
|--------|----------|----------|-----------|-------------|------------|-----------|-------------|------------------|
| LoRA | L1 | r=16 | | | | | | |
| DoRA | L1 | r=16 | | | | | | |
| GaLore | L1 | r=16 | | | | | | |
| TTLoRA | L2 | χ=16 | | | | | | |
| TRG | L2 | χ=16 | | | | | | |
| MPO | L2 | χ=16 | | | | | | |
| QTHA | L2 | χ=16 | | | | | | |
| iPEPS | L3 | χ=16 | | | | | | |
| LowRankSketching→LoRA | L3 | r* | | | | | | |
| DecoherenceReg+LoRA | L4 | λ=0.1 | | | | | | |
| **GV-ALR + LoRA** | L1/L3 | — | | | | | | |
| **DataReupload + LoRA** | L2/L3 | K passes | | | | | | |
| **FrozenBackbone + LoRA** | L2/L3 | last 2 blocks | | | | | | |

Footnote every row with `DataSchedule`, `DatasetVersion`, `StudentModel`.

---

## References (starting bibliography)

| Topic | Pointer |
|-------|---------|
| CompactifAI / MPO for LLMs | arXiv / ResearchGate — tensor decomposition for attention and MLP |
| QTHA | arXiv — quantum tensor hybrid adaptation vs LoRA |
| TT-LoRA | arXiv — tensor train decomposition for PEFT |
| TRG / iPEPS fine-tuning | arXiv — iPEPS-TRG training time benchmarks |
| GaLore | ICML CoLoRAI workshop — gradient subspace methods |
| DoRA | Standard PEFT documentation — magnitude-direction decomposition |
| CoLoRAI ICML 2026 | Low-rank identifiability, sketching, completion |
| GV-ALR / Re-upload / Hybrid head | [QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md) — quantun-ia exp_015/008/037+ |

Exact citations to be filled when implementation pins library versions.

---

## Agent protocol

1. Never claim a method is "novel physics" — use **Evidence** labels.
2. Tensor methods **must** log `bondDimension` (χ) in `TrainingRunCompleted`.
3. `DecoherenceRegularization` runs **must** be labeled L4 Speculative in reports.
4. Compare methods at **matched trainable parameter count** when possible, not only matched χ/rank symbol.
