# CI Pipeline — nano-coder

> GitHub Actions workflow: `.github/workflows/ci.yml`
> Modeled after [quantun-ia CI](https://github.com/AlexandreZanata/quantun-ia/blob/main/.github/workflows/ci.yml).

---

## Triggers

- Push / PR to `main`, `master`, `develop`
- Weekly schedule (Monday 06:00 UTC) — dependency drift detection

---

## Jobs

| Job | Purpose | Blocks merge |
|-----|---------|--------------|
| **Lint** | `ruff check scripts/ tests/ experiments/` | Yes |
| **Documentation Structure** | `scripts/validate_docs.py` + MIT LICENSE | Yes |
| **Hypothesis Placeholder Check** | `tests/unit/test_hypothesis.py` | Yes |
| **Agent Harness Smoke** | `agent-harness/tests/smoke.sh` | Yes |
| **Unit & Contract Tests** | `pytest tests/ -m "not real"` | Yes |
| **Research Contracts** | `tests/contracts/` | Yes |
| **Paper Build (LaTeX)** | `pdflatex paper/main.tex` | No (`continue-on-error: true`) |

---

## Local equivalent

```bash
make check
# = lint + docs-check + hypothesis-check + harness-smoke + test
```

---

## What CI does NOT run

- GPU training (`tests/real/`) — local RTX 4060 only
- Full publication-profile benchmarks — operator manual
- Teacher LLM API calls — secrets not in CI

---

## Badges (README)

```markdown
[![CI](https://github.com/AlexandreZanata/nano-coder/actions/workflows/ci.yml/badge.svg)](...)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
```

Update URL when repository is published.

---

## Adding CI checks

1. Add test under `tests/contracts/` or `tests/unit/`
2. Wire into `make check` in [Makefile](../Makefile)
3. Add job or step in `.github/workflows/ci.yml`
4. Document here

---

## Agent harness in CI

Every PR validates:

```bash
pip install -r agent-harness/requirements.txt
./agent-harness/tests/smoke.sh
```

Ensures rule resolution and manifest integrity remain intact.
