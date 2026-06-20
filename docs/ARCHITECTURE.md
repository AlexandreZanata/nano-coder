# Architecture — nano-coder

> Layered design for the distillation and benchmark pipeline. Stack-agnostic contract; implementation may use Python CLI + HuggingFace + API clients.

---

## Bounded contexts

| Context | Responsibility |
|---------|----------------|
| **DataGeneration** | Seeds, synthetic expansion, quality gates, dataset versioning |
| **Training** | Student model fine-tuning (Full, LoRA, QLoRA, incremental vs mixed) |
| **Evaluation** | Held-out tests, Pass@k, cost metrics, LLM-as-judge |
| **Reporting** | Comparative tables, experiment artifacts, final report |

Contexts communicate via **domain events** and **immutable dataset artifacts** — never direct cross-context calls from Domain.

---

## Layer diagram

```
INTERFACES          CLI commands, config files (YAML/JSON), report outputs
       ↓
APPLICATION         Use cases: generate dataset, filter, train, benchmark, export report
       ↓
DOMAIN              Entities, aggregates, business rules, state machines, events
       ↑
INFRASTRUCTURE      Teacher LLM API, HuggingFace, GPU runners, parsers/linters, filesystem
```

**Rule:** Domain imports nothing from Infrastructure. Application orchestrates; Infrastructure implements ports.

---

## Aggregates and roots

### SyntheticDataset (root: `SyntheticDataset`)

- Contains `SyntheticExample` records grouped by `TargetLanguage`
- Enforces minimum quality and size thresholds before `Published`
- Emits `DatasetPublished`, `ExampleRejected`

### DatasetGenerationRun (root: `DatasetGenerationRun`)

- Owns lifecycle from `Pending` → `Generating` → `Filtering` → `Completed` | `Failed`
- References target `TargetLanguage` and seed set

### TrainingRun (root: `TrainingRun`)

- Links `StudentModel`, `TrainingMethod`, `DatasetVersion`
- Owns training lifecycle and artifact paths (Infrastructure stores files; Domain tracks status)

### BenchmarkRun (root: `BenchmarkRun`)

- Links trained model checkpoint (or baseline), `HeldOutTestSet`, metric configuration
- Produces immutable `EvaluationResult` snapshots

---

## Value objects

| Value object | Invariants |
|--------------|------------|
| `TargetLanguage` | Must be `JavaScript`, `HTML`, or `FreeMarker` |
| `CompressionMethod` | Must be enum in [TRAINING-METHODS.md](TRAINING-METHODS.md) |
| `DataSchedule` | Must be `MixedLanguages`, `IncrementalByLanguage`, or `SingleLanguage` |
| `BondDimension` | Must be 4, 8, 16, or 32 when tensor method used |
| `EvidenceLevel` | Must be Established, QuantumInspired, NovelApplication, or Speculative |
| `QualityScore` | Float 0.0–1.0; reject if below configured threshold |
| `DatasetVersion` | Non-empty, unique per published dataset |
| `Instruction` | Non-empty string, max length configured in pipeline config |
| `GeneratedCode` | Non-empty string; language must match `TargetLanguage` |

---

## Access control (RBAC)

Phase 1 is **local single-operator** — no multi-tenant API.

| Role | Actions |
|------|---------|
| `PipelineOperator` | Run all pipeline stages, approve manual review samples, publish datasets |
| `ReadOnlyReviewer` | View reports and datasets; cannot trigger training or API spend |

Future HTTP dashboard (if added) must enforce this matrix per `docs/SECURITY.md`.

---

## Directory layout (planned)

```
src/
├── domain/           # Entities, VOs, rules, state machines
├── application/      # Use case handlers
├── infrastructure/   # LLM clients, HF trainers, validators
└── interfaces/       # CLI entrypoints

data/
├── seeds/            # Gold seed examples (tracked, small)
├── datasets/         # Published SyntheticDataset artifacts (gitignored large files)
├── checkpoints/      # Model checkpoints (gitignored)
└── benchmarks/       # HeldOutTestSet + results

configs/
├── pipeline.yaml     # Global pipeline config
└── experiments/      # Per-experiment overrides
```

---

## Key references

| Document | Purpose |
|----------|---------|
| [GLOSSARY.md](GLOSSARY.md) | Ubiquitous language |
| [BUSINESS-RULES.md](BUSINESS-RULES.md) | Named BRs (GIVEN/WHEN/THEN) |
| [STATE-MACHINES.md](STATE-MACHINES.md) | Entity transitions |
| [DOMAIN-EVENTS.md](DOMAIN-EVENTS.md) | Event catalog |
| [PIPELINE-CONTRACT.md](PIPELINE-CONTRACT.md) | CLI and config contract |
| [PHASES.md](PHASES.md) | Experiment phases |
