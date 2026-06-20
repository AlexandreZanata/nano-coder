# Results — EXP 003 (DoRA vs LoRA)

**Status:** Completed (real GPU, smoke profile, parallel batch)  
**Date:** 2026-06-20  
**Run IDs:** `train-dora-smoke-001` / `bench-dora-smoke-001`  
**Consolidated report:** [docs/WAVE1-GPU-RESULTS.md](../../docs/WAVE1-GPU-RESULTS.md#model-3--dora-exp_003)

## What happened

Real DoRA fine-tuning (PEFT `use_dora=True`, rank 16) on **Qwen2.5-Coder-0.5B** completed on **RTX 4060 Laptop GPU (8 GB)**, launched in parallel with LoRA and QLoRA smoke runs (`max_parallel=3`).

| Metric | Value |
|--------|-------|
| Dataset | `ds-2026-06-20-js-v1` (10 JS examples) |
| Profile | `smoke` |
| Train steps | 5 |
| Final loss | 1.980 |
| Trainable params | 2,211,840 (+2.3% vs LoRA) |
| Peak VRAM | 1.495 GB |
| Train wall-clock | 10.5 s |
| Pass@1 / Pass@5 | **20.0%** / 33.3% |
| Syntax validity | **60.0%** |
| Backend | `hf-peft-dora` |

**Per language (Pass@1 / Pass@5 / syntax):**

| Language | Pass@1 | Pass@5 | Syntax |
|----------|--------|--------|--------|
| JavaScript | 20% | 40% | 40% |
| HTML | 20% | 40% | 40% |
| FreeMarker | 20% | 20% | 100% |

**vs smoke-profile peers (same parallel batch):**

| Method | Pass@1 | Pass@5 | VRAM | Trainable params |
|--------|--------|--------|------|------------------|
| LoRA | 0.0% | 33.3% | 1.495 GB | 2,162,688 |
| QLoRA | 6.7% | 26.7% | 1.245 GB | 2,162,688 |
| **DoRA** | **20.0%** | 33.3% | 1.495 GB | 2,211,840 |

Replay:

```bash
python3 experiments/exp_003_dora_baseline/run.py --profile smoke --real
# or parallel batch:
python3 scripts/run_wave1_gpu_parallel.py --profile smoke --real --max-parallel 3
```

## Comparison with hypothesis

**Partially supported at smoke scale.** Hypothesis expected DoRA ≥3% Pass@1 above LoRA on HTML and FreeMarker. Observed **+20 pp Pass@1 aggregate** vs LoRA (20% vs 0%) with gains on all three languages at 5-task subsets. Param count differs by 2.3% (within 10% footnote threshold).

Results remain non-conclusive for publication claims — 10 training examples and 5 eval tasks per language.

## Unexpected finding

DoRA achieved the **highest Pass@1 and syntax validity** of the three Wave 1 PEFT methods in the parallel smoke batch, despite only +49k trainable parameters over LoRA. FreeMarker syntax validity reached 100% (5/5 tasks syntactically valid).

## Suggested next experiment

Run **fewshot_baseline** benchmark and Phase 5 ranking across all four Wave 1 methods at the same `datasetVersion`, then repeat smoke/publication profiles once dataset ≥ 1,500 examples per language is published.
