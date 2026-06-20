# Use Case Template

> Copy this file per use case: `docs/use-cases/UC-NNN-short-title.md`

**Active use cases:**

| ID | Title |
|----|-------|
| UC-001 | [Generate synthetic dataset](use-cases/UC-001-generate-synthetic-dataset.md) |
| UC-002 | [Publish synthetic dataset](use-cases/UC-002-publish-dataset.md) |
| UC-003 | [Fine-tune student model](use-cases/UC-003-fine-tune-student.md) |
| UC-004 | [Run benchmark](use-cases/UC-004-run-benchmark.md) |
| UC-005 | [Export experiment report](use-cases/UC-005-export-report.md) |

---

# Use Case: UC-XXX — _(Title)_

---

## Metadata

| Field | Value |
|-------|-------|
| ID | UC-XXX |
| Actor | _(who executes)_
| Status | Draft |

## Preconditions

- _(what must be true before execution)_

## Main flow (happy path)

1. _(step)_
2. _(step)_
3. _(step)_

## Alternate flows

### AF-1: _(name)_

- **When:** _(condition)_
- **Then:** _(outcome)_

## Business rules applied

| Rule ID | Description |
|---------|-------------|
| BR-XXX | _(GIVEN/WHEN/THEN reference)_ |

## Domain events raised

| Event | When |
|-------|------|
| `SomethingHappened` | _(after which step)_ |

## Authorization

| Role | Allowed |
|------|---------|
| _(RoleName)_ | Yes / No |

## Out of scope

- _(explicit exclusions)_
