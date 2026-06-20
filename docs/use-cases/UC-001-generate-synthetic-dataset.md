# Use Case: UC-001 — Generate Synthetic Dataset

---

## Metadata

| Field | Value |
|-------|-------|
| ID | UC-001 |
| Actor | PipelineOperator |
| Status | Accepted |

## Preconditions

- At least 50 `GoldSeedExample` records exist for the target `TargetLanguage` (BR-001)
- `pipeline.yaml` configured with `TeacherModel` credentials in environment
- `maxBudgetUsd` set

## Main flow (happy path)

1. Operator runs `nano-coder generate dataset --language <lang> --run-id <id>`.
2. Application creates `DatasetGenerationRun` in `Pending`.
3. System validates seed count → transitions to `Generating`.
4. TeacherModel expands seeds via Self-Instruct / Evol-Instruct batch loop.
5. Each candidate emits `SyntheticExampleGenerated`.
6. Quality gates run → `ExampleAccepted` or `ExampleRejected`.
7. When target count reached, run transitions to `AwaitingManualReview`.
8. Operator reviews 5% sample and approves.
9. Run → `Completed`; draft dataset written to `data/datasets/draft/{run-id}/`.

## Alternate flows

### AF-1: Budget exceeded

- **When:** API cost exceeds `maxBudgetUsd` during step 4
- **Then:** Run → `Failed` (BR-006); partial draft retained but not publishable

### AF-2: Insufficient seeds

- **When:** Seed count < 50 at step 2
- **Then:** Abort with `SEED_COUNT_INSUFFICIENT`; no API calls

## Business rules applied

| Rule ID | Description |
|---------|-------------|
| BR-001 | Minimum 50 gold seeds |
| BR-002 | Quality gate mandatory |
| BR-003 | Syntax validation per language |
| BR-006 | Teacher spend guardrail |

## Domain events raised

| Event | When |
|-------|------|
| `SyntheticExampleGenerated` | After each teacher response |
| `ExampleRejected` | Gate failure |
| `ExampleAccepted` | All gates pass |

## Authorization

| Role | Allowed |
|------|---------|
| PipelineOperator | Yes |
| ReadOnlyReviewer | No |

## Out of scope

- Publishing dataset (see UC-002)
- Training student model
