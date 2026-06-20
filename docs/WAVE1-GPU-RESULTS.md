# Wave 1 GPU Results — RTX 4060 Laptop (8 GB)

**Hardware:** NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB  
**Student model:** Qwen2.5-Coder-0.5B (`Qwen/Qwen2.5-Coder-0.5B`)  
**Dataset (validation):** `ds-2026-06-20-js-v1` (10 JS examples)  
**Benchmark subset:** 5 held-out tasks per language (15 total)  
**Backend:** HuggingFace + PEFT + TRL SFT (`--real`)

---

## Parallel smoke batch (3 models, ~16 min wall-clock)

Launched with `scripts/run_wave1_gpu_parallel.py --profile smoke --real --max-parallel 3`.  
Peak VRAM per job ~1.25–1.50 GB — fits 3 concurrent jobs on 8 GB.

| Model | Method | Run IDs | Loss | Pass@1 | Pass@5 | VRAM | Train (s) |
|-------|--------|---------|------|--------|--------|------|-----------|
| 1 | LoRA | `train-lora-smoke-001` | 1.99 | 0.0% | 33.3% | 1.50 | 9.5 |
| 2 | QLoRA | `train-qlora-smoke-001` | 2.09 | 6.7% | 26.7% | 1.25 | 10.6 |
| 3 | DoRA | `train-dora-smoke-001` | 1.98 | **20.0%** | 33.3% | 1.50 | 10.5 |

**Ranking (Pass@1, smoke):** DoRA > QLoRA > LoRA

LaTeX: [paper/tables/wave1-smoke-results.tex](../paper/tables/wave1-smoke-results.tex)

---

## Model 1 — LoRA (exp_001)

| Field | ci | smoke (parallel) |
|-------|-----|------------------|
| Pass@1 / Pass@5 | 0.0% / 33.3% | 0.0% / 33.3% |
| Peak VRAM | 1.504 GB | 1.495 GB |
| Train time | 39.7 s | 9.5 s |

Detail: [experiments/exp_001_lora_baseline/results.md](../experiments/exp_001_lora_baseline/results.md)

---

## Model 2 — QLoRA (exp_002)

| Field | ci | smoke (parallel) |
|-------|-----|------------------|
| Pass@1 / Pass@5 | **6.7%** / 26.7% | **6.7%** / 26.7% |
| Peak VRAM | **1.247 GB** | **1.245 GB** |
| Train time | **10.9 s** | 10.6 s |
| Backend | `hf-peft-qlora` | `hf-peft-qlora` |

### vs Model 1 (LoRA, ci profile)

| Metric | LoRA | QLoRA | Delta |
|--------|------|-------|-------|
| Peak VRAM | 1.504 GB | 1.247 GB | **−17%** |
| Train time | 39.7 s | 10.9 s | **−73%** |
| Pass@1 | 0.0% | 6.7% | +6.7 pp |
| Pass@5 | 33.3% | 26.7% | −6.6 pp |

**Per language (smoke, Pass@1 / Pass@5 / syntax):** JS 0/40/20 · HTML 0/20/0 · FMT 20/20/80

Detail: [experiments/exp_002_qlora_baseline/results.md](../experiments/exp_002_qlora_baseline/results.md)

---

## Model 3 — DoRA (exp_003)

| Field | smoke (parallel) |
|-------|------------------|
| Pass@1 / Pass@5 | **20.0%** / 33.3% |
| Syntax validity | **60.0%** |
| Peak VRAM | 1.495 GB |
| Trainable params | 2,211,840 (+2.3% vs LoRA) |
| Backend | `hf-peft-dora` |

**Per language (Pass@1 / Pass@5 / syntax):** JS 20/40/40 · HTML 20/40/40 · FMT 20/20/100

Detail: [experiments/exp_003_dora_baseline/results.md](../experiments/exp_003_dora_baseline/results.md)

---

## Model 4 — FewShot baseline

_Pending — run via Phase 3 Wave 1 orchestrator._

---

## Paper tables

| Profile | LaTeX |
|---------|-------|
| ci (sequential validation) | [paper/tables/wave1-ci-results.tex](../paper/tables/wave1-ci-results.tex) |
| smoke (parallel batch) | [paper/tables/wave1-smoke-results.tex](../paper/tables/wave1-smoke-results.tex) |

PDF: `make paper-build`

---

## Replay

```bash
make install-gpu

# Single experiment
python3 experiments/exp_002_qlora_baseline/run.py --profile smoke --real

# 3 models in parallel (8 GB VRAM)
make wave1-gpu-parallel
# or:
python3 scripts/run_wave1_gpu_parallel.py --profile smoke --real --max-parallel 3
```
