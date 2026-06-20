# State Machines — nano-coder

> Valid transitions only. Invalid transitions throw domain exceptions.

---

## DatasetGenerationRun

| State | Description |
|-------|-------------|
| `Pending` | Created, not started |
| `Generating` | TeacherModel producing candidates |
| `Filtering` | Quality gates running |
| `AwaitingManualReview` | Sample queue for PipelineOperator |
| `Completed` | Dataset artifact written; not yet Published |
| `Failed` | Terminal — error or budget exceeded |
| `Cancelled` | Terminal — operator aborted |

### Transitions

| From | To | Trigger | Role |
|------|-----|---------|------|
| `Pending` | `Generating` | `start()` | PipelineOperator |
| `Generating` | `Filtering` | generation batch complete | System |
| `Generating` | `Failed` | budget exceeded / API error | System |
| `Filtering` | `AwaitingManualReview` | manual sample threshold reached | System |
| `Filtering` | `Completed` | all gates pass, no review required | System |
| `AwaitingManualReview` | `Completed` | operator approves sample | PipelineOperator |
| `AwaitingManualReview` | `Failed` | operator rejects run | PipelineOperator |
| `Pending` \| `Generating` \| `Filtering` | `Cancelled` | `cancel()` | PipelineOperator |

Terminal: `Failed`, `Cancelled`. `Completed` allows downstream publish on `SyntheticDataset`.

---

## SyntheticDataset (publication)

| State | Description |
|-------|-------------|
| `Draft` | Mutable; examples can be added/removed |
| `Published` | Immutable snapshot; referenced by DatasetVersion |
| `Archived` | Terminal; superseded by newer version |

### Transitions

| From | To | Trigger | Role |
|------|-----|---------|------|
| `Draft` | `Published` | `publish()` when BR-005 satisfied | PipelineOperator |
| `Published` | `Archived` | new Published version supersedes | System |

Terminal: `Archived`. `Published` datasets are never edited — corrections = new version.

---

## TrainingRun

| State | Description |
|-------|-------------|
| `Pending` | Config validated, waiting for GPU/resources |
| `Running` | Fine-tuning in progress |
| `Completed` | Checkpoint written |
| `Failed` | Terminal — OOM, NaN loss, config error |
| `Cancelled` | Terminal — operator stopped |

### Transitions

| From | To | Trigger | Role |
|------|-----|---------|------|
| `Pending` | `Running` | `start()` and BR-007 satisfied | PipelineOperator |
| `Running` | `Completed` | training loop finished | System |
| `Running` | `Failed` | unrecoverable error | System |
| `Pending` \| `Running` | `Cancelled` | `cancel()` | PipelineOperator |

---

## BenchmarkRun

| State | Description |
|-------|-------------|
| `Pending` | Model and test set bound |
| `Running` | Generating samples and scoring |
| `Completed` | EvaluationResult persisted |
| `Failed` | Terminal |

### Transitions

| From | To | Trigger | Role |
|------|-----|---------|------|
| `Pending` | `Running` | `start()` and BR-008 satisfied | PipelineOperator |
| `Running` | `Completed` | all tasks scored | System |
| `Running` | `Failed` | infrastructure error | System |

---

## ExperimentPhase (project-level)

| State | Description |
|-------|-------------|
| `SyntheticDataGeneration` | Phase 1 |
| `StudentModelSelection` | Phase 2 |
| `TrainingComparison` | Phase 3 |
| `Evaluation` | Phase 4 |
| `Reporting` | Phase 5 |
| `Done` | Terminal |

Phases advance sequentially; skipping requires documented ADR exception.
