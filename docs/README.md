# Documentation Index — nano-coder

> All docs in English. Complete [NEW-PROJECT-CHECKLIST.md](NEW-PROJECT-CHECKLIST.md) before implementation.

---

## Start here

| Document | Purpose |
|----------|---------|
| [RESEARCH-LAB-STRUCTURE.md](RESEARCH-LAB-STRUCTURE.md) | **quantun-ia-style lab layout** |
| [PHASES.md](PHASES.md) | Five experiment phases |
| [GLOSSARY.md](GLOSSARY.md) | Ubiquitous language |
| [NEW-PROJECT-CHECKLIST.md](NEW-PROJECT-CHECKLIST.md) | Pre-implementation gate |

---

## Research & paper

| Document | Purpose |
|----------|---------|
| [HYPOTHESIS-WORKFLOW.md](HYPOTHESIS-WORKFLOW.md) | hypothesis → run → results |
| [EXPERIMENTS.md](EXPERIMENTS.md) | Experiment registry (exp_001–010) |
| [PAPER-NARRATIVE.md](PAPER-NARRATIVE.md) | In-scope paper claims |
| [REPRODUCIBILITY.md](REPRODUCIBILITY.md) | Replication checklist |
| [CI.md](CI.md) | GitHub Actions pipeline |
| [TESTING.md](TESTING.md) | Two-tier CI + GPU gate |
| [COMPUTE-ENVIRONMENT.md](COMPUTE-ENVIRONMENT.md) | RTX 4060 guidance |
| [../paper/README.md](../paper/README.md) | LaTeX build |

---

## Domain

| Document | Purpose |
|----------|---------|
| [BUSINESS-RULES.md](BUSINESS-RULES.md) | BR-001–BR-014 (GIVEN/WHEN/THEN) |
| [STATE-MACHINES.md](STATE-MACHINES.md) | Run and dataset lifecycles |
| [DOMAIN-EVENTS.md](DOMAIN-EVENTS.md) | Event catalog |

---

## Interfaces and evaluation

| Document | Purpose |
|----------|---------|
| [PIPELINE-CONTRACT.md](PIPELINE-CONTRACT.md) | CLI commands, config, artifacts (**primary interface**) |
| [API-CONTRACT.md](API-CONTRACT.md) | Future HTTP API (not phase 1) |
| [EVALUATION-METHOD.md](EVALUATION-METHOD.md) | Pass@k, metrics, smoke test gates |
| [TRAINING-METHODS.md](TRAINING-METHODS.md) | **Full PEFT/tensor benchmark catalog** |
| [QUANTUN-IA-PROVEN-METHODS.md](QUANTUN-IA-PROVEN-METHODS.md) | **Top 3 quantun-ia methods for transfer** |

---

## Use cases

| ID | File |
|----|------|
| UC-001 | [generate-synthetic-dataset](use-cases/UC-001-generate-synthetic-dataset.md) |
| UC-002 | [publish-dataset](use-cases/UC-002-publish-dataset.md) |
| UC-003 | [fine-tune-student](use-cases/UC-003-fine-tune-student.md) |
| UC-004 | [run-benchmark](use-cases/UC-004-run-benchmark.md) |
| UC-005 | [export-report](use-cases/UC-005-export-report.md) |

Template: [USE-CASE-EXAMPLE.md](USE-CASE-EXAMPLE.md)

---

## Architecture decisions

| ADR | Title |
|-----|-------|
| [ADR-001](adr/ADR-001-layered-pipeline-architecture.md) | Layered pipeline architecture |
| [ADR-002](adr/ADR-002-student-model-selection.md) | Student model selection (Proposed) |
| [ADR-003](adr/ADR-003-synthetic-data-distillation.md) | Synthetic data via teacher distillation |
| [ADR-004](adr/ADR-004-training-methods-benchmark.md) | Baseline training methods matrix |
| [ADR-005](adr/ADR-005-advanced-peft-benchmark.md) | Advanced PEFT + tensor networks |
| [ADR-006](adr/ADR-006-quantun-ia-proven-transfers.md) | quantun-ia top-3 transfer methods |

---

## Security

| Document | Purpose |
|----------|---------|
| [SECURITY.md](SECURITY.md) | OWASP 2025 + Agentic 2026 mapping |

---

## Agent harness

| Path | Purpose |
|------|---------|
| [../AGENTS.md](../AGENTS.md) | Agent session entry point |
| [../agent-rules/AGENT-CORE-PRINCIPLES.md](../agent-rules/AGENT-CORE-PRINCIPLES.md) | Global architecture contract |

Resolve task-specific rules:

```bash
./agent-harness/resolve-rules.sh domain layer state agent security
```
