# Results — EXP 002 (QLoRA Baseline)

**Status:** Completed (real GPU, ci profile)  
**Date:** 2026-06-20  
**Run IDs:** `train-qlora-ci-001` / `bench-qlora-ci-001`  
**Consolidated report:** [docs/WAVE1-GPU-RESULTS.md](../../docs/WAVE1-GPU-RESULTS.md#parallel-smoke-batch-3-models-16-min-wall-clock)

## What happened

Real QLoRA fine-tuning (4-bit base + LoRA rank 16) on **Qwen2.5-Coder-0.5B** completed on **NVIDIA RTX 4060 Laptop GPU (8 GB)**.

| Metric | Value |
|--------|-------|
| Dataset | `ds-2026-06-20-js-v1` (10 JS examples) |
| Profile | `ci` |
| Train steps | 5 |
| Final loss | 2.094 |
| Trainable params | 2,162,688 |
| Peak VRAM (train) | 1.247 GB |
| Train wall-clock | 10.9 s |
| Benchmark tasks | 15 (5 per language) |
| Pass@1 (aggregate) | 6.7% |
| Pass@5 (aggregate) | 26.7% |
| Syntax validity | 33.3% |
| Backend | `hf-peft-qlora` |

**Per language (Pass@1 / Pass@5 / syntax):**

| Language | Pass@1 | Pass@5 | Syntax |
|----------|--------|--------|--------|
| JavaScript | 0% | 40% | 20% |
| HTML | 0% | 20% | 0% |
| FreeMarker | 20% | 20% | 80% |

**vs exp_001 (LoRA, same profile):**

| Metric | LoRA | QLoRA | Delta |
|--------|------|-------|-------|
| Peak VRAM | 1.504 GB | 1.247 GB | −17% |
| Train time | 39.7 s | 10.9 s | −73% |
| Pass@1 | 0.0% | 6.7% | +6.7 pp |
| Pass@5 | 33.3% | 26.7% | −6.6 pp |

Replay:

```bash
python3 experiments/exp_002_qlora_baseline/run.py --profile ci --real
```

## Comparison with hypothesis

**Partially supported on VRAM; inconclusive on Pass@1 at smoke scale.**

Hypothesis expected QLoRA within 2% Pass@1 of LoRA with ≥20% lower VRAM. Observed **17% VRAM reduction** (1.247 vs 1.504 GB) — slightly below the 20% target but meaningful on 8 GB hardware. Pass@1 is **higher** for QLoRA (6.7% vs 0%) but both are far below publication thresholds; Pass@5 is slightly lower for QLoRA.

At 10 training examples, metric differences are noise — the primary validation is that QLoRA trains and benchmarks end-to-end on RTX 4060.

## Publication profile — M1 dataset (2026-06-21)

**Status:** Completed (real GPU, `publication` profile)  
**Run IDs:** `train-qlora-publication-001` / `bench-qlora-publication-001`  
**Dataset:** `ds-2026-06-21-mixed-m2000-v2` (2,100 examples; 1,500 used for train)

| Metric | Value |
|--------|-------|
| Train steps | 500 |
| Final train loss | 0.086 |
| Peak VRAM (train) | 2.74 GB |
| Train wall-clock | 477.6 s |
| Pass@1 (aggregate) | **13.3%** |
| Pass@5 (aggregate) | **26.7%** |

**vs ci smoke (10 examples):** Pass@1 6.7% → **13.3%** (+6.6 pp).  
**vs exp_001 LoRA publication (same dataset):** Pass@1 6.7% → **13.3%** (QLoRA higher).

Replay:

```bash
python3 experiments/exp_002_qlora_baseline/run.py \
  --profile publication \
  --dataset-version ds-2026-06-21-mixed-m2000-v2 \
  --real
```

**Smoke parallel batch (2026-06-20):** Re-run at `smoke` profile in parallel with LoRA and DoRA (`train-qlora-smoke-001`). Metrics unchanged vs ci: Pass@1 6.7%, Pass@5 26.7%, VRAM 1.245 GB.

## Publication profile — Tier-A OSS dataset (2026-06-21)

**Status:** Completed (real GPU, `publication` profile)  
**Run IDs:** `train-qlora-publication-001` / `bench-qlora-publication-001`  
**Dataset:** `ds-2026-06-21-mixed-tier-a-v1` (5,818 examples; 1,500 used for train)

| Metric | Value |
|--------|-------|
| Train steps | 500 |
| Final train loss | 0.463 |
| Peak VRAM (train) | 2.76 GB |
| Train wall-clock | 908 s |
| Pass@1 (aggregate) | **6.7%** |
| Pass@5 (aggregate) | **20.0%** |

**vs M1 mixed:** Pass@1 13.3% → **6.7%** (−6.6 pp); Pass@5 26.7% → **20.0%** (−6.7 pp).  
**vs exp_001 LoRA (same Tier-A dataset):** Pass@1 **6.7%** vs 0.0% (QLoRA still ahead).

Replay:

```bash
python3 experiments/exp_002_qlora_baseline/run.py \
  --profile publication \
  --dataset-version ds-2026-06-21-mixed-tier-a-v1 \
  --real
```

## Unexpected finding

QLoRA training was **3.6× faster** wall-clock than full-precision LoRA (10.9 s vs 39.7 s) despite similar step count — likely due to 4-bit matmul and `prepare_model_for_kbit_training` path. FreeMarker Pass@1 hit 20% (one task) while LoRA had 0% Pass@1 on FMT.

## Suggested next experiment

Run **exp_003 (DoRA)** at matched rank and ci profile, then repeat all Wave 1 anchors at **publication profile** once dataset ≥ 1,500 examples per language is published.
