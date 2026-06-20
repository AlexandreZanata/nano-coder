# Use Case: UC-005 — Export Experiment Report

---

## Metadata

| Field | Value |
|-------|-------|
| ID | UC-005 |
| Actor | PipelineOperator |
| Status | Accepted |

## Preconditions

- At least two `BenchmarkRun` records in `Completed` state (different methods or languages)
- All runs document same `HeldOutTestSet` version OR footnotes prepared (BR-012)

## Main flow (happy path)

1. Operator runs `nano-coder report export --run-ids <ids> --output ./reports/final.md`.
2. Application loads benchmark artifacts and training metadata.
3. Builds method × language × metric tables per [EVALUATION-METHOD.md](../EVALUATION-METHOD.md).
4. Includes cost columns (VRAM, train time, inference throughput).
5. Adds research question answers and negative findings section.
6. Writes Markdown + JSON summary.
7. `ExperimentReportGenerated` event emitted.

## Alternate flows

### AF-1: Incomparable runs

- **When:** Mixed `DatasetVersion` without `--allow-mixed` flag
- **Then:** Warn and require explicit footnote in output (BR-012)

## Business rules applied

| Rule ID | Description |
|---------|-------------|
| BR-012 | Report comparability |

## Domain events raised

| Event | When |
|-------|------|
| `ExperimentReportGenerated` | Step 7 |

## Authorization

| Role | Allowed |
|------|---------|
| PipelineOperator | Yes |
| ReadOnlyReviewer | Yes (read exported report) |

## Out of scope

- Automated publication to external sites
- Statistical significance testing (optional future work)
