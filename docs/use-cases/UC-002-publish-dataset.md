# Use Case: UC-002 — Publish Synthetic Dataset

---

## Metadata

| Field | Value |
|-------|-------|
| ID | UC-002 |
| Actor | PipelineOperator |
| Status | Accepted |

## Preconditions

- `DatasetGenerationRun` in `Completed` state
- Draft contains ≥ 1,500 accepted examples for target language(s)
- ≥ 90% passed `SyntaxValidation`
- Manual review sample (≥ 5%) approved by operator

## Main flow (happy path)

1. Operator runs `nano-coder dataset publish --draft-id <id> --version <version>`.
2. Application validates BR-005 thresholds.
3. `SyntheticDataset` transitions `Draft` → `Published`.
4. Immutable snapshot written to `data/datasets/{version}/`.
5. `DatasetPublished` event emitted with `DatasetVersion`.

## Alternate flows

### AF-1: Threshold not met

- **When:** Example count or quality ratio below threshold at step 2
- **Then:** Publish rejected with explicit counts; dataset remains Draft

## Business rules applied

| Rule ID | Description |
|---------|-------------|
| BR-005 | Dataset publish thresholds |
| BR-007 | Published state required before training |

## Domain events raised

| Event | When |
|-------|------|
| `DatasetPublished` | After successful publish |

## Authorization

| Role | Allowed |
|------|---------|
| PipelineOperator | Yes |
| ReadOnlyReviewer | No |

## Out of scope

- Editing published datasets (create new version instead)
