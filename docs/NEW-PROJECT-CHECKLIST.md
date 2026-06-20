# New Project Checklist

> Complete **before writing the first line of application code**.
> Mirrors `agent-rules/AGENT-CORE-PRINCIPLES.md` checklist.

---

## Architecture and domain

- [x] **Layers defined** — [ARCHITECTURE.md](ARCHITECTURE.md)
- [x] **Entities and aggregates** — SyntheticDataset, DatasetGenerationRun, TrainingRun, BenchmarkRun
- [x] **Value Objects** — TargetLanguage, CompressionMethod, BondDimension, EvidenceLevel ([ARCHITECTURE.md](ARCHITECTURE.md), [GLOSSARY.md](GLOSSARY.md))
- [x] **Business rules** — BR-001–BR-014 ([BUSINESS-RULES.md](BUSINESS-RULES.md))
- [x] **State machines** — [STATE-MACHINES.md](STATE-MACHINES.md)
- [x] **Access roles** — PipelineOperator, ReadOnlyReviewer ([ARCHITECTURE.md](ARCHITECTURE.md))
- [x] **Domain events** — [DOMAIN-EVENTS.md](DOMAIN-EVENTS.md)
- [x] **Use cases** — UC-001–UC-005 ([use-cases/](use-cases/))
- [x] **API contract** — Phase 1 CLI: [PIPELINE-CONTRACT.md](PIPELINE-CONTRACT.md); HTTP deferred: [API-CONTRACT.md](API-CONTRACT.md)
- [x] **Glossary** — [GLOSSARY.md](GLOSSARY.md)

---

## Security (OWASP)

- [x] **OWASP Top 10:2025** — [SECURITY.md](SECURITY.md)
- [x] **Agentic 2026 (ASI01–ASI10)** — [SECURITY.md](SECURITY.md) + BR-009

---

## Agent harness

- [x] **Harness installed** — `agent-rules/`, `agent-harness/`, `.cursor/rules/` (local)
- [x] **AGENTS.md** — project entry point at repo root

---

## Experiment design

- [x] **Phases documented** — [PHASES.md](PHASES.md)
- [x] **Evaluation method** — [EVALUATION-METHOD.md](EVALUATION-METHOD.md)
- [x] **ADRs** — [adr/](adr/) (001–005)
- [x] **Training methods catalog** — [TRAINING-METHODS.md](TRAINING-METHODS.md)
- [x] **Research lab structure** — [RESEARCH-LAB-STRUCTURE.md](RESEARCH-LAB-STRUCTURE.md) (quantun-ia model)
- [x] **MIT License** — [LICENSE](../LICENSE) + [CITATION.cff](../CITATION.cff)
- [x] **CI pipeline** — [.github/workflows/ci.yml](../.github/workflows/ci.yml) · [CI.md](CI.md)
- [x] **Experiments exp_001–010** — hypothesis-first stubs registered
- [x] **Paper skeleton** — [paper/main.tex](../paper/main.tex)
- [ ] **Gold seeds authored** — 50–100 per language in `data/seeds/` (operator task)
- [ ] **Student smoke test** — ADR-002 gate before full training matrix
- [ ] **Stack chosen** — Python version, HF, trainer lib (next implementation step)

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Product / domain | _(owner)_ | 2026-06-20 |
| Tech lead | _(owner)_ | 2026-06-20 |

**Documentation gate passed.** Implementation may begin with domain layer + CLI scaffold.

Remaining operator tasks: author gold seeds, run Phase 2 smoke test, choose Python dependencies.
