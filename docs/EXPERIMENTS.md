# Experiment Registry — nano-coder

> Central index. Config: [config/experiments.yaml](../config/experiments.yaml).
> Workflow: [HYPOTHESIS-WORKFLOW.md](HYPOTHESIS-WORKFLOW.md).

---

## Wave 1 — Anchors (Required)

| ID | Folder | Method | Evidence | Hypothesis summary |
|----|--------|--------|----------|-------------------|
| 001 | `exp_001_lora_baseline` | LoRA r=16 | L1 | Primary baseline for Pass@1 / VRAM |
| 002 | `exp_002_qlora_baseline` | QLoRA | L1 | Lowest VRAM established method |
| 003 | `exp_003_dora_baseline` | DoRA r=16 | L1 | Beats LoRA on template-heavy HTML/FMT |

---

## Wave 2 — Tensor entry + speed (Required)

| ID | Folder | Method | Evidence | Hypothesis summary |
|----|--------|--------|----------|-------------------|
| 004 | `exp_004_ttloRA_bond_sweep` | TTLoRA χ∈{4,8,16,32} | L2 | Matches LoRA at lower params |
| 005 | `exp_005_trg_training_speed` | TRG χ=16 | L2 | ≥30% faster wall-clock vs LoRA |
| 006 | `exp_006_galore_memory` | GaLore | L1 | Full-FT-like updates at LoRA memory |

---

## Wave 3 — Aggressive compression (Recommended)

| ID | Folder | Method | Evidence | Hypothesis summary |
|----|--------|--------|----------|-------------------|
| 007 | `exp_007_mpo_compression` | MPO | L2 | Fewer params than LoRA at same Pass@1 |
| 008 | `exp_008_qtha_rank_limit` | QTHA χ=8 | L2 | Beats LoRA-r=8 on JS logic tasks |

---

## Wave 4 — Exploratory (Optional)

| ID | Folder | Method | Evidence | Hypothesis summary |
|----|--------|--------|----------|-------------------|
| 009 | `exp_009_incremental_vs_mixed` | LoRA + schedules | L1 | Incremental wins for 0.5B |
| 010 | `exp_010_decoherence_regularization` | L4 + LoRA | L4 | Null result acceptable |

---

## Wave Q — quantun-ia proven transfers (Recommended)

| ID | Folder | Method | Evidence | Hypothesis summary |
|----|--------|--------|----------|-------------------|
| 011 | `exp_011_gv_alr_lora_transfer` | GV-ALR + LoRA | L3 | ≥25% faster; ≤1 pp Pass@1 drop |
| 012 | `exp_012_reupload_schedule_lora` | DataReupload + LoRA | L3 | ≥3 pp vs single-pass |
| 013 | `exp_013_frozen_backbone_lora` | FrozenBackbone + LoRA | L3 | ≤2 pp vs full LoRA; ≥20% VRAM saved |

Evidence source: [QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md)

---

## Running experiments

```bash
# CI profile (CPU stub until training implemented)
MLFLOW_DISABLE=1 python experiments/exp_001_lora_baseline/run.py --profile ci

# Publication (RTX 4060)
MLFLOW_DISABLE=1 python experiments/exp_001_lora_baseline/run.py --profile publication
```

---

## Logs

All runs append to `logs/experiments.jsonl`:

```json
{
  "experiment_id": "exp_001_lora_baseline",
  "compression_method": "LoRA",
  "evidence_level": "Established",
  "bond_dimension": null,
  "lora_rank": 16,
  "pass_at_1": {},
  "peak_vram_gb": null,
  "duration_seconds": null
}
```

---

## Adding experiment 011+

1. Copy `experiments/template/`
2. Register in `config/experiments.yaml`
3. Add row here and [PAPER-NARRATIVE.md](PAPER-NARRATIVE.md) if in-scope
