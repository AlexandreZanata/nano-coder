# Research Lab Structure — nano-coder

> Adapted from [quantun-ia](https://github.com/AlexandreZanata/quantun-ia) — hypothesis-first, append-only logs, CI gates, paper pipeline.
> **License:** MIT — see [LICENSE](../LICENSE).

---

## Reference repository

| quantun-ia | nano-coder equivalent |
|------------|----------------------|
| Quantum vs classical QML benchmarks | SLM PEFT / tensor-network benchmarks for code |
| `experiments/exp_NNN_*/` | Same — one folder per benchmark run |
| `hypothesis.md` → `run.py` → `results.md` | Same discipline |
| `config/experiments.yaml` | Central hyperparameters + profiles |
| `logs/experiments.jsonl` | Append-only JSONL metrics (gitignored) |
| `paper/main.tex` + `make paper-build` | LaTeX paper from benchmark tables |
| `make check` / `make check-real` | CI (CPU) vs GPU gate (RTX 4060) |
| `docs/paper_narrative.md` | [PAPER-NARRATIVE.md](PAPER-NARRATIVE.md) |
| `CITATION.cff` + Zenodo | Same open-science path |
| Agent Harness | `agent-rules/` + `agent-harness/` |

---

## Repository layout

```
nano-coder/
├── LICENSE                    # MIT
├── CITATION.cff               # Citation metadata
├── CONTRIBUTING.md            # PR + hypothesis-first rules
├── Makefile                   # check, paper-build, health-gpu
├── pyproject.toml             # pytest, ruff, coverage ≥80%
├── requirements-dev.txt
│
├── config/
│   └── experiments.yaml       # All experiment hyperparameters
│
├── experiments/
│   ├── template/              # Copy to create new exp
│   └── exp_NNN_<name>/        # hypothesis.md, run.py, results.md
│
├── src/                       # Domain + training (implementation)
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── interfaces/
│
├── tests/
│   ├── unit/                  # hypothesis placeholder check
│   ├── contracts/             # YAML ↔ folders ↔ paper narrative
│   ├── integration/           # CLI smoke (future)
│   └── real/                  # RTX 4060 GPU gate (@pytest.mark.real)
│
├── logs/
│   └── experiments.jsonl      # Append-only (gitignored)
│
├── data/
│   ├── seeds/                 # Gold seeds (small, tracked)
│   ├── datasets/              # Large artifacts (gitignored)
│   ├── checkpoints/           # gitignored
│   └── benchmarks/            # gitignored
│
├── paper/
│   ├── main.tex
│   ├── sections/
│   ├── tables/                # Auto-generated LaTeX
│   ├── figures/               # Pass@k heatmaps, χ sweeps
│   └── arxiv_metadata.yaml
│
├── docs/                      # Domain + research docs
├── agent-rules/               # Agent Harness rules
└── agent-harness/             # Rule resolution tooling
```

---

## Research workflow (five steps)

```
1. Write hypothesis.md     (before any code)
2. Register config/experiments.yaml
3. Implement run.py thin orchestrator → src/
4. Run → append logs/experiments.jsonl
5. Fill results.md → sync to paper/
```

See [HYPOTHESIS-WORKFLOW.md](HYPOTHESIS-WORKFLOW.md).

---

## CI vs local GPU gate

| Tier | Command | Where | Purpose |
|------|---------|-------|---------|
| **1 — CI** | `make check` | GitHub Actions CPU | Lint, docs, hypothesis, contracts, harness |
| **2 — Real** | `make check-real` | Local RTX 4060 | Actual LoRA/tensor training smoke |

See [CI.md](CI.md) and [TESTING.md](TESTING.md).

---

## Paper pipeline

```bash
make paper-build          # paper/main.pdf
# Future: make latex-tables, make figures, make arxiv-bundle
```

Narrative scope: [PAPER-NARRATIVE.md](PAPER-NARRATIVE.md).

---

## Key docs map

| Topic | Document |
|-------|----------|
| Domain language | [GLOSSARY.md](GLOSSARY.md) |
| Training methods | [TRAINING-METHODS.md](TRAINING-METHODS.md) |
| Experiment registry | [EXPERIMENTS.md](EXPERIMENTS.md) |
| Reproducibility | [REPRODUCIBILITY.md](REPRODUCIBILITY.md) |
| Compute (4060) | [COMPUTE-ENVIRONMENT.md](COMPUTE-ENVIRONMENT.md) |
| Agent entry | [../AGENTS.md](../AGENTS.md) |

---

## Open science checklist

- [x] MIT license
- [x] `CITATION.cff`
- [x] Hypothesis-first experiments
- [x] CI validation on every PR
- [ ] Pinned `requirements.lock` (when HF stack added)
- [ ] Zenodo DOI (post v0.1.0 tag)
- [ ] arXiv upload (post paper build)
