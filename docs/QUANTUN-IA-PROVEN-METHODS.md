# quantun-ia Proven Methods — Transfer Candidates for nano-coder

> **Source lab:** [quantun-ia](https://github.com/AlexandreZanata/quantun-ia) (MicroQML Bench v1, RTX 4060 publication runs).
> **Purpose:** Methods with the **strongest empirical success** in quantun-ia benchmarks, documented here as **future research objects** alongside quantum/tensor PEFT methods in [TRAINING-METHODS.md](TRAINING-METHODS.md).
> **Honesty:** Success in tabular/QML classification does **not** guarantee transfer to code SLMs — each method gets a pre-registered falsification criterion in nano-coder.

---

## Selection criteria

From quantun-ia `results.md` corpus (80+ experiments, exp_068 grand synthesis C1–C4):

| Criterion | Weight |
|-----------|--------|
| Holm-significant holdout win **or** accepted efficiency gate | Required |
| Cross-domain replication (≥2 anchors) | High |
| RTX 4060 publication evidence | Required |
| Not contradicted by `docs/negative_results.md` headline | Required |

**Top 3 selected** (ranked by replicability + effect size):

| Rank | Method | quantun-ia code | Primary evidence |
|------|--------|-----------------|------------------|
| 1 | **GV-ALR** | `GradientVarianceAdaptiveLR` | exp_054 + exp_075 accepted; exp_015 Holm win vs shallow QNN |
| 2 | **Data Re-upload** | `DataReupload` | exp_008 + exp_001 Holm-significant vs basic QNN |
| 3 | **Frozen-Backbone Hybrid Head** | `FrozenBackboneHybridHead` | exp_037/051/062/071 accepted on all 4 domain anchors |

Methods **not** promoted despite hype: entanglement schedules (exp_053/074 rejected), quantum warm-start (exp_052 rejected), curriculum margin (exp_005 rejected). See quantun-ia [negative_results.md](https://github.com/AlexandreZanata/quantun-ia/blob/main/docs/negative_results.md).

---

## 1. GV-ALR — Gradient-Variance Adaptive Learning Rate

| Field | Value |
|-------|-------|
| **Code name (nano-coder)** | `GradientVarianceAdaptiveLR` |
| **quantun-ia module** | `src/training/adaptive_lr.py` |
| **Evidence in quantun-ia** | **L1 Established** (optimization); validated on quantum circuits |
| **Relation to nano-coder Tier 1** | Complements `GaLore` — both adapt optimization dynamics; GV-ALR scales LR from gradient variance, GaLore projects gradient subspace |

### Benchmark results (quantun-ia)

| Experiment | Domain | Result | Verdict |
|------------|--------|--------|---------|
| exp_015 | Synthetic circles | adaptive 6q×3l vs 4q fixed: **+7.8 pp**, Cohen's d=1.40, Holm p=0.012 | **Significant** |
| exp_015 | Synthetic circles | adaptive vs fixed 6q: +5.3 pp, d=0.78, p=0.059 | Inconclusive (underpowered) |
| exp_054 | HIGGS (C1) | Same val AUC (Δ=0.01 pp); **5/8 epochs**; wall-time **59%** | **Accepted** efficiency gate |
| exp_075 | NIHR (C2) | Same val PR-AUC (Δ=−0.24 pp); **5/8 epochs**; wall-time **58%** | **Accepted** replication |

### Why it ranks #1

- Only method with **accepted cross-domain efficiency replication** (physics + clinical) on RTX 4060
- Statistically significant accuracy win vs shallower baseline (exp_015)
- Documented algorithm: [quantun-ia/docs/method_adaptive_lr.md](https://github.com/AlexandreZanata/quantun-ia/blob/main/docs/method_adaptive_lr.md)

### nano-coder transfer hypothesis

```
GIVEN a StudentModel fine-tuned with LoRA on mixed JS/HTML/FreeMarker data
WHEN GV-ALR replaces fixed Adam LR on the adapter parameters
THEN Pass@1 stays within 1 pp of fixed LR
AND wall-clock training time drops by ≥25% on RTX 4060
```

**Planned experiment:** `exp_011_gv_alr_lora_transfer` (Wave Q)

---

## 2. Data Re-upload — Multi-Pass Layer Injection

| Field | Value |
|-------|-------|
| **Code name (nano-coder)** | `DataReupload` |
| **quantun-ia concept** | Re-inject classical/quantum features between variational layers |
| **Evidence in quantun-ia** | **L2 QuantumInspired** (circuit technique); strong synthetic wins |
| **Relation to tensor methods** | Analogous to increasing effective depth without linear param growth — related to TRG coarse-graining intuition |

### Benchmark results (quantun-ia)

| Experiment | Comparison | Δ holdout | p-value | Verdict |
|------------|------------|-----------|---------|---------|
| exp_008 | reupload vs basic QNN | **+5.6 pp** | 0.012 | **Holm-significant** |
| exp_001 | reupload vs basic 4q | **+7.6 pp** | 0.002 | **Significant** |
| exp_001 | classical_32 vs reupload | +7.3 pp | 0.002 | Classical still wins vs shallow reupload |
| exp_002 | QuantumFirst (reupload) vs ClassicalFirst | **+4.6 pp** | Holm 0.012 | **Significant** architecture win |

### Why it ranks #2

- **Largest consistent accuracy lift** over the naive baseline (basic QNN) across seeds
- Enables QuantumFirst architecture (65.7% vs 61.1% ClassicalFirst on circles)
- Clear falsification: reupload vs single-pass at matched param budget

### nano-coder transfer hypothesis

```
GIVEN synthetic code examples presented once per epoch (standard LoRA)
WHEN DataReupload schedule re-presents each batch K times with shifted layer targets
  (JS: logic layers; HTML: nesting layers; FMT: macro scope layers)
THEN Pass@1 improves by ≥3 pp vs single-pass at matched total token budget
```

**SLM mapping:** Not quantum circuits — **multi-pass fine-tune** with re-injected embeddings between adapter blocks (inspired by re-upload, not a literal QNN port).

**Planned experiment:** `exp_012_reupload_schedule_lora` (Wave Q)

---

## 3. Frozen-Backbone Hybrid Head — Train Head Only

| Field | Value |
|-------|-------|
| **Code name (nano-coder)** | `FrozenBackboneHybridHead` |
| **quantun-ia pattern** | Freeze LargeNanoMLP (~1.1M params); train hybrid QNN head (~289 params) |
| **Evidence in quantun-ia** | **L2 QuantumInspired** (hybrid head); **best cross-domain replication** |
| **Relation to LoRA** | Conceptually closest to **LoRA on last layers only** with frozen base — nano-coder already plans LoRA; this method adds quantun-ia's proven freeze protocol |

### Benchmark results (quantun-ia) — four-anchor panel

| Experiment | Domain | Anchor | Δ vs classical head | Gate | Verdict |
|------------|--------|--------|----------------------|------|---------|
| exp_037 | Physics | HIGGS (C1) | **+0.04 pp** AUC | ≥ −1.0 pp | **Accepted** |
| exp_051 | Clinical | NIHR (C2) | **+0.02 pp** PR-AUC | ≥ −1.0 pp | **Accepted** |
| exp_062 | Agro-climate | ACYD (C4) | −0.19 pp AUC | ≥ −1.0 pp | **Accepted** |
| exp_071 | Software | GoBug (C3) | hybrid vs classical head | ≥ −1.0 pp | **Accepted** |

exp_068 grand synthesis: **only recipe with wins across multiple domains** without catastrophic regression; hybrid head never violated the −1.0 pp gate on any anchor.

### Why it ranks #3

- **4/4 domain anchors passed** the pre-registered gate (unique among quantum recipes)
- Extreme parameter efficiency: ~289 trainable params on ~1.1M frozen backbone
- Directly maps to SLM practice: **freeze Qwen 0.5B, LoRA only on lm_head + last N layers**

### nano-coder transfer hypothesis

```
GIVEN Qwen2.5-Coder-0.5B fully frozen except lm_head + last 2 transformer blocks
WHEN LoRA adapters train on synthetic JS/HTML/FreeMarker data
THEN Pass@1 is within 2 pp of full LoRA on all layers
AND peak VRAM drops by ≥20%
AND trainable params drop by ≥60%
```

**Planned experiment:** `exp_013_frozen_backbone_lora` (Wave Q)

---

## Integration with quantum/tensor methods (nano-coder)

### Combined research matrix

| Tier | Source | Methods |
|------|--------|---------|
| T0 | ADR-004 | FewShot, LoRA, QLoRA, FullFineTune |
| T1 | Literature | DoRA, GaLore |
| **TQ** | **quantun-ia proven** | **GV-ALR, DataReupload, FrozenBackboneHybridHead** |
| T2 | Tensor / quantum-inspired | MPO, QTHA, TTLoRA, TRG, iPEPS |
| T3 | Exploratory | LowRankSketching, DecoherenceRegularization |

### Recommended Wave Q (after Wave 1 LoRA anchor)

```
exp_011  GV-ALR + LoRA        — efficiency at parity Pass@1
exp_012  DataReupload + LoRA  — multi-pass schedule
exp_013  FrozenBackbone + LoRA — VRAM/param efficiency
```

Then combine best Wave Q method with best Wave 2 tensor method (e.g. TTLoRA + GV-ALR).

---

## Evidence cross-reference (quantun-ia paths)

| Method | Read first |
|--------|------------|
| GV-ALR | `experiments/exp_054_adaptive_hybrid_higgs/results.md`, `exp_075_adaptive_hybrid_nihr/results.md`, `docs/method_adaptive_lr.md` |
| Data Re-upload | `experiments/exp_008_data_reupload/results.md`, `exp_001_quantum_vs_classical/results.md` |
| Frozen Hybrid Head | `experiments/exp_037_hybrid_nano_higgs/results.md`, `exp_051_quantum_head_nihr/results.md`, `exp_062_hybrid_nano_acyd_soy/results.md`, `exp_071_hybrid_nano_gobug/results.md` |

Grand synthesis: `experiments/exp_068_nano_grand_comparison/results.md`

---

## Agent protocol

1. Cite quantun-ia experiment IDs when proposing Wave Q runs.
2. Do **not** claim QML wins imply code SLM wins — transfer is **hypothesis**.
3. Report `EvidenceLevel`: GV-ALR = L1; DataReupload and FrozenBackboneHybridHead = L2 for nano-coder until replicated locally.
4. Negative transfer results are valid — document beside quantun-ia positive results.
