# Use Case: UC-003 — Fine-Tune Student Model

---

## Metadata

| Field | Value |
|-------|-------|
| ID | UC-003 |
| Actor | PipelineOperator |
| Status | Accepted |

## Preconditions

- `SyntheticDataset` in `Published` state with known `DatasetVersion`
- `StudentModel` base weights available locally or via HuggingFace
- GPU resources meet method requirements (QLoRA needs less VRAM than FullFineTune)
- Operator confirmed training config

## Main flow (happy path)

1. Operator runs `nano-coder train --compression-method <method> --data-schedule <schedule> ...`.
2. Application validates BR-007 (dataset published) and method-specific hyperparams (χ, rank, λ).
3. `TrainingRun` created in `Pending`.
4. Infrastructure loads dataset, applies `TrainingMethod` (LoRA adapters, etc.).
5. Run → `Running`; `TrainingRunStarted` emitted.
6. Training completes; checkpoint saved.
7. Run → `Completed`; `TrainingRunCompleted` with duration and peak VRAM.

## Alternate flows

### AF-1: OOM during full fine-tune

- **When:** GPU out of memory in step 4 with `FullFineTune`
- **Then:** Run → `Failed`; operator retries with `QLoRA` or smaller batch

### AF-2: Incremental by language

- **When:** `TrainingMethod` is `IncrementalByLanguage`
- **Then:** Sequential runs per language; each checkpoint tagged (BR-011)

## Business rules applied

| Rule ID | Description |
|---------|-------------|
| BR-007 | Human confirm / published dataset required |
| BR-011 | Incremental checkpoint tagging |
| BR-013 | Evidence level + bondDimension logged |
| BR-014 | Matched param budget for comparisons |

## Domain events raised

| Event | When |
|-------|------|
| `TrainingRunStarted` | Step 5 |
| `TrainingRunCompleted` | Step 7 |
| `TrainingRunFailed` | On error |

## Authorization

| Role | Allowed |
|------|---------|
| PipelineOperator | Yes |
| ReadOnlyReviewer | No |

## Out of scope

- Benchmark evaluation (UC-004)
- Hyperparameter search automation (manual config only in phase 1)
