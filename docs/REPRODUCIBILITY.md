# Reproducibility — nano-coder

> NeurIPS-style reproducibility statement. Modeled after quantun-ia.

---

## 1. Code availability

| Item | Status | Evidence |
|------|--------|----------|
| Public repository | Planned | `CITATION.cff` → repository-code |
| License | ✅ | MIT — [LICENSE](../LICENSE) |
| Citation metadata | ✅ | [CITATION.cff](../CITATION.cff) |
| Contribution guide | ✅ | [CONTRIBUTING.md](../CONTRIBUTING.md) |

---

## 2. Dependencies and environment

| Item | Status | Evidence |
|------|--------|----------|
| Dev deps | ✅ | `requirements-dev.txt` |
| Python version | ✅ | `>=3.11` (CI uses 3.12) |
| Pinned training stack | Pending | `requirements.lock` when HF/PEFT added |
| GPU optional | ✅ | `make health-gpu`, `@pytest.mark.real` |

**Install:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
make check
```

---

## 3. Random seeds and held-out isolation

| Item | Status | Evidence |
|------|--------|----------|
| Seeds in config | ✅ | `config/experiments.yaml` — publication: 5 seeds |
| Held-out isolation | ✅ | BR-004, [EVALUATION-METHOD.md](EVALUATION-METHOD.md) |
| Dataset versioning | ✅ | `DatasetVersion` immutable snapshots |
| Seed logged per run | Planned | `ExperimentLogger` → JSONL |

Publication seeds: `42, 123, 456, 789, 1024`

---

## 4. Compute profiles

| Profile | Examples | Steps | Seeds | Hardware | Est. runtime |
|---------|----------|-------|-------|----------|--------------|
| `ci` | 50 | 20 | 1 | CPU | ~30 s per exp stub |
| `smoke` | 200 | 100 | 1 | GPU | ~5 min (Phase 2 gate) |
| `publication` | 1500 | 500 | 5 | RTX 4060 | ~20–60 min per method |

**Commands:**

```bash
make reviewer-repro              # ~5 min CPU verification
make check-real                  # GPU gate (local)
python experiments/exp_001_lora_baseline/run.py --profile ci
python experiments/exp_001_lora_baseline/run.py --profile publication
```

---

## 5. Experiment artifacts

| Artifact | Location | Versioned |
|----------|----------|-----------|
| Append-only logs | `logs/experiments.jsonl` | Gitignored |
| Published datasets | `data/datasets/{version}/` | DVC / release (future) |
| Checkpoints | `data/checkpoints/` | Gitignored |
| Benchmark JSON | `data/benchmarks/{run-id}/` | Gitignored |
| Paper tables | `paper/tables/` | Generated, committed after publication run |

---

## 6. Replication checklist for reviewers

1. Clone repo; `pip install -r requirements-dev.txt`
2. `make reviewer-repro`
3. Run `exp_001` with `--profile ci` — compare JSONL schema
4. For GPU claims: `make health-gpu` then `make check-real`
5. Compare your `results.md` metrics to paper tables

Open issue with: experiment ID, profile, commit SHA, your Pass@1, verdict.

---

## 7. Known limitations (pre-register)

- Synthetic-only training data — gap vs manual gold reported explicitly
- Sub-1B models may fail complex JS — valid negative finding
- L4 DecoherenceRegularization may show null effect
- Tensor libraries may not support all student models at 0.5B
