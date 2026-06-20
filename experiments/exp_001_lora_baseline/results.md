# Results — EXP 001 (LoRA Baseline)

**Status:** Completed (real GPU, ci profile)  
**Date:** 2026-06-20  
**Run IDs:** `train-lora-ci-001` / `bench-lora-ci-001`  
**Consolidated report:** [docs/WAVE1-GPU-RESULTS.md](../../docs/WAVE1-GPU-RESULTS.md#model-1--lora-exp_001)

## What happened

Real LoRA fine-tuning on **Qwen2.5-Coder-0.5B** (HF + PEFT + TRL SFT) completed on **NVIDIA RTX 4060 Laptop GPU (8 GB)**.

| Metric | Value |
|--------|-------|
| Dataset | `ds-2026-06-20-js-v1` (10 JS examples) |
| Profile | `ci` |
| Train steps | 5 |
| Final loss | 1.994 |
| Trainable params | 2,162,688 |
| Peak VRAM (train) | 1.504 GB |
| Train wall-clock | 39.7 s |
| Benchmark tasks | 15 (5 per language, realMaxTasksPerLanguage) |
| Pass@1 (aggregate) | 0.0% |
| Pass@5 (aggregate) | 33.3% |
| Syntax validity | 46.7% |
| Backend | `hf-peft-lora` |

**Per language (Pass@1 / Pass@5 / syntax):**

| Language | Pass@1 | Pass@5 | Syntax |
|----------|--------|--------|--------|
| JavaScript | 0% | 40% | 40% |
| HTML | 0% | 40% | 20% |
| FreeMarker | 0% | 20% | 80% |

Replay:

```bash
python3 experiments/exp_001_lora_baseline/run.py --profile ci --real
```

## Comparison with hypothesis

**Hypothesis not supported** at this data scale. Expected Pass@1 ≥ 60% on smoke held-out; observed **0%** Pass@1 aggregate.

This is consistent with **BR-005 smoke constraint**: 10 training examples is a pipeline validation run, not a publication-quality dataset (target ≥ 1,500 examples per language). VRAM (1.5 GB) is well below the 7 GB falsification threshold.

## Unexpected finding

FreeMarker showed the highest syntax validity (80%) despite zero Pass@1 hits — the model produces structurally valid templates but fails acceptance criteria. Pass@5 > 0 on JS/HTML suggests occasional criterion satisfaction with sampling.

## Suggested next experiment

Run **exp_002 (QLoRA)** at the same profile and dataset version for matched VRAM comparison before scaling to publication dataset.
