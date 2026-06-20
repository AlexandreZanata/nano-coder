# Testing — nano-coder

> Two-tier validation modeled after quantun-ia.

---

## Test pyramid

```
tests/
├── unit/           # Hypothesis placeholders, pure domain (future)
├── contracts/      # experiments.yaml ↔ folders ↔ paper narrative
├── integration/    # CLI smoke (future)
└── real/           # RTX 4060 GPU gate (@pytest.mark.real)
```

---

## Two-tier validation

| Tier | Command | Environment | Purpose |
|------|---------|-------------|---------|
| **1 — CI gate** | `make check` | GitHub Actions CPU | Docs, hypothesis, contracts, harness — not scientific truth |
| **2 — Real gate** | `make check-real` | Local RTX 4060 | Actual training smoke — mandatory before publication numbers |

Real tests skip when CUDA unavailable (CI never runs them).

---

## Running tests

```bash
make check                    # full CI gate locally
make test                     # pytest only
make hypothesis-check         # experiment hypotheses
make docs-check               # structure validation
make harness-smoke            # agent-harness
make coverage                 # ≥80% when src/ exists
make check-real               # GPU (local)
```

---

## Coverage thresholds

| Metric | Minimum | Config |
|--------|---------|--------|
| Statements | 80% | `pyproject.toml` |

Until `src/` is implemented, CI runs tests without `--cov-fail-under` hard gate on empty src.

---

## CI pipeline

See [CI.md](CI.md). Jobs: Lint, Docs, Hypothesis, Harness, Unit, Contracts, Paper Build.

---

## Contract tests

| File | Validates |
|------|-----------|
| `tests/contracts/test_research_structure.py` | YAML registry, paper narrative, MIT license |
| `tests/unit/test_hypothesis.py` | No template placeholders in exp_* hypotheses |

Future:

- `tests/contracts/test_jsonl_schema.py` — experiment log schema
- `tests/contracts/test_paper_narrative.py` — LaTeX scope vs narrative

---

## Health check

```bash
make health       # logs writable, optional pdflatex
make health-gpu   # + CUDA probe
```
