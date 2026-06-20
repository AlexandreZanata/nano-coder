# nano-coder

[![CI](https://github.com/AlexandreZanata/nano-coder/actions/workflows/ci.yml/badge.svg)](https://github.com/AlexandreZanata/nano-coder/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Fine-tune **Small Language Models** (sub-1B–3B) for **JavaScript**, **HTML**, and **FreeMarker** using **synthetic teacher distillation** — then benchmark PEFT and quantum-**inspired** tensor methods (LoRA → TT-LoRA → MPO) with bond dimension χ on **RTX 4060-class** hardware.

**Research lab structure:** modeled after [quantun-ia](https://github.com/AlexandreZanata/quantun-ia) — hypothesis-first experiments, append-only logs, CI gates, paper pipeline. **License:** MIT.

---

## Quick start

```bash
git clone git@github.com:AlexandreZanata/nano-coder.git
cd nano-coder

python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

make check                    # CI gate locally
make reviewer-repro           # ~5 min reviewer smoke

# Run experiment stub (training stack pending)
MLFLOW_DISABLE=1 python experiments/exp_001_lora_baseline/run.py --profile ci

make paper-build              # paper/main.pdf (requires pdflatex)
```

---

## What it does

1. **Generate** synthetic JS/HTML/FreeMarker datasets from gold seeds + teacher LLM
2. **Train** student SLMs with 14+ compression methods ([TRAINING-METHODS.md](docs/TRAINING-METHODS.md))
3. **Evaluate** Pass@k, VRAM, wall-clock; χ × language heatmaps
4. **Publish** reproducible paper + JSONL logs

Negative results are valid outcomes.

---

## Research workflow

```
hypothesis.md  →  run.py  →  logs/experiments.jsonl  →  results.md  →  paper/
```

See [docs/HYPOTHESIS-WORKFLOW.md](docs/HYPOTHESIS-WORKFLOW.md) and [docs/RESEARCH-LAB-STRUCTURE.md](docs/RESEARCH-LAB-STRUCTURE.md).

---

## Experiments (Waves 1–4)

| ID | Method | Wave |
|----|--------|------|
| exp_001 | LoRA baseline | 1 |
| exp_002 | QLoRA | 1 |
| exp_003 | DoRA | 1 |
| exp_004 | TT-LoRA χ sweep | 2 |
| exp_005 | TRG speed | 2 |
| exp_006 | GaLore | 2 |
| exp_007 | MPO | 3 |
| exp_008 | QTHA | 3 |
| exp_009 | Incremental vs mixed | 4 |
| exp_010 | Decoherence reg. (L4) | 4 |

Full registry: [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) · Config: [config/experiments.yaml](config/experiments.yaml)

---

## CI & testing

```bash
make check          # lint + docs + hypothesis + harness + tests
make check-real     # RTX 4060 GPU gate (local only)
```

Pipeline: [docs/CI.md](docs/CI.md) · Testing: [docs/TESTING.md](docs/TESTING.md)

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/README.md](docs/README.md) | Full index |
| [docs/RESEARCH-LAB-STRUCTURE.md](docs/RESEARCH-LAB-STRUCTURE.md) | quantun-ia mapping |
| [docs/PAPER-NARRATIVE.md](docs/PAPER-NARRATIVE.md) | Paper scope |
| [docs/TRAINING-METHODS.md](docs/TRAINING-METHODS.md) | Method catalog |
| [CONTRIBUTING.md](CONTRIBUTING.md) | PR checklist |
| [AGENTS.md](AGENTS.md) | Agent harness entry |

---

## Citation

See [CITATION.cff](CITATION.cff). MIT License — [LICENSE](LICENSE).
