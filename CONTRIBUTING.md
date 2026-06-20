# Contributing to nano-coder

Thank you for contributing. This project follows **hypothesis-first research discipline**
adapted from [quantun-ia](https://github.com/AlexandreZanata/quantun-ia).

**Language:** 100% English — code, comments, docs, commits, and agent output.

## Prerequisites

- Python 3.11+ (3.12 recommended for CI parity)
- Read [docs/RESEARCH-LAB-STRUCTURE.md](docs/RESEARCH-LAB-STRUCTURE.md) before your first PR
- Familiarity with PEFT, HuggingFace, and pytest

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
make check
```

## Hypothesis-first rule (mandatory)

Every experiment **must** have a non-placeholder `hypothesis.md` written **before** `run.py` runs.

1. Copy `experiments/template/` → `experiments/exp_NNN_descriptive_name/`
2. Register in `config/experiments.yaml`
3. Fill `hypothesis.md` (expectation, reasoning, falsification, metrics)
4. Write thin `run.py` — logic lives in `src/`
5. After running, fill `results.md`

CI rejects placeholder hypothesis text via `tests/unit/test_hypothesis.py`.

## Adding a new experiment

1. Create `experiments/exp_NNN_<name>/` with the three artifacts
2. Add entry under `experiments:` in `config/experiments.yaml`
3. Log metrics through `ExperimentLogger` (`src/training/metrics.py` when implemented)
4. Enforce held-out isolation (BR-004) and evidence labels (BR-013)
5. Add smoke import in `tests/smoke/` if new modules are introduced

## Configuration

- Hyperparameters in `config/experiments.yaml` — never hardcode in `run.py`
- Profiles: `ci` (fast CPU smoke), `publication` (full benchmark), `smoke` (Phase 2 gate)
- Training methods: see [docs/TRAINING-METHODS.md](docs/TRAINING-METHODS.md)

## Running checks

```bash
make lint           # ruff
make check          # lint + docs + hypothesis + unit tests + harness smoke
make check-real     # RTX 4060 GPU gate (local only, skipped in CI)
make paper-build    # LaTeX PDF (optional, continue-on-error in CI)
```

## Pull request checklist

- [ ] `hypothesis.md` exists with no template placeholders
- [ ] `results.md` updated if experiment was run
- [ ] `config/experiments.yaml` updated for new/changed experiments
- [ ] `make check` passes locally
- [ ] `logs/experiments.jsonl` **not** committed (append-only, gitignored)
- [ ] No secrets in code, configs, or logs
- [ ] Evidence level documented for tensor/speculative methods (BR-013)
- [ ] English only in all new artifacts

## Log discipline

- `logs/experiments.jsonl` is **append-only** — never delete entries
- Always use `ExperimentLogger` — never write directly to `logs/`
- Never log API keys, tokens, or PII

## References

- [Hypothesis workflow](docs/HYPOTHESIS-WORKFLOW.md)
- [Research lab structure](docs/RESEARCH-LAB-STRUCTURE.md)
- [CI pipeline](docs/CI.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Paper narrative](docs/PAPER-NARRATIVE.md)
