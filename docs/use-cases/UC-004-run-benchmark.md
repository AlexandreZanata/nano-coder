# Use Case: UC-004 — Run Benchmark

---

## Metadata

| Field | Value |
|-------|-------|
| ID | UC-004 |
| Actor | PipelineOperator |
| Status | Accepted |

## Preconditions

- Trained checkpoint exists OR baseline `FewShot` config defined
- `HeldOutTestSet` version matches experiment config (BR-008)
- No held-out leakage in training data (BR-004)

## Main flow (happy path)

1. Operator runs `nano-coder benchmark --checkpoint <path> --test-set-version held-out-v1 --run-id <id>`.
2. Application validates test set version and leakage checks.
3. `BenchmarkRun` → `Running`; `BenchmarkRunStarted` emitted.
4. For each held-out task: generate k samples, run `CorrectnessCheck`.
5. Aggregate Pass@1, Pass@5, latency, model size.
6. Optional: LLM-as-judge on 10% sample.
7. Results written to `data/benchmarks/{run-id}/`.
8. Run → `Completed`; `BenchmarkRunCompleted` emitted.

## Alternate flows

### AF-1: Test set version mismatch

- **When:** Config test set version ≠ requested at step 2
- **Then:** Abort with `TEST_SET_VERSION_MISMATCH`

### AF-2: FewShot baseline

- **When:** No checkpoint; `--method FewShot` with prompt template
- **Then:** Same evaluation path; checkpoint id tagged `baseline-fewshot`

## Business rules applied

| Rule ID | Description |
|---------|-------------|
| BR-004 | Held-out isolation |
| BR-008 | Frozen test set version |
| BR-010 | Judge is advisory |
| BR-012 | Comparability metadata stored |

## Domain events raised

| Event | When |
|-------|------|
| `BenchmarkRunStarted` | Step 3 |
| `BenchmarkRunCompleted` | Step 8 |

## Authorization

| Role | Allowed |
|------|---------|
| PipelineOperator | Yes |
| ReadOnlyReviewer | No (may view results after) |

## Out of scope

- Final comparative report (UC-005)
