# Domain Events — nano-coder

> Past-tense names. Immutable once persisted. Payload includes id, timestamp, origin.

---

## DataGeneration context

### `GoldSeedImported`

| Field | Type | Description |
|-------|------|-------------|
| `seedId` | string | Unique seed identifier |
| `targetLanguage` | TargetLanguage | Language of the example |
| `importedBy` | string | PipelineOperator id |

**When:** After manual seed files are validated and registered.

---

### `SyntheticExampleGenerated`

| Field | Type | Description |
|-------|------|-------------|
| `exampleId` | string | Candidate example id |
| `runId` | string | DatasetGenerationRun id |
| `targetLanguage` | TargetLanguage | Output language |
| `teacherModel` | string | Model id used |

**When:** TeacherModel returns a candidate pair (before quality gates).

---

### `ExampleRejected`

| Field | Type | Description |
|-------|------|-------------|
| `exampleId` | string | Rejected example |
| `gateType` | QualityGate | Which gate failed |
| `reason` | string | Safe, non-sensitive reason code |

**When:** Any QualityGate fails (BR-002).

---

### `ExampleAccepted`

| Field | Type | Description |
|-------|------|-------------|
| `exampleId` | string | Accepted example |
| `datasetId` | string | Draft SyntheticDataset |

**When:** All required gates pass.

---

### `DatasetPublished`

| Field | Type | Description |
|-------|------|-------------|
| `datasetVersion` | DatasetVersion | Immutable version id |
| `targetLanguages` | TargetLanguage[] | Languages included |
| `exampleCount` | number | Total accepted examples |
| `publishedBy` | string | PipelineOperator id |

**When:** SyntheticDataset transitions Draft → Published (BR-005).

---

## Training context

### `TrainingRunStarted`

| Field | Type | Description |
|-------|------|-------------|
| `trainingRunId` | string | Run identifier |
| `studentModel` | string | Base model id |
| `trainingMethod` | TrainingMethod | Method enum |
| `datasetVersion` | DatasetVersion | Training data version |

**When:** TrainingRun Pending → Running.

---

### `TrainingRunCompleted`

| Field | Type | Description |
|-------|------|-------------|
| `trainingRunId` | string | Run identifier |
| `compressionMethod` | CompressionMethod | Method used |
| `dataSchedule` | DataSchedule | Language schedule |
| `evidenceLevel` | EvidenceLevel | L1–L4 label (BR-013) |
| `bondDimension` | number | χ if tensor method; null otherwise |
| `loraRank` | number | Rank if LoRA-family; null otherwise |
| `trainableParamCount` | number | For matched comparisons (BR-014) |
| `checkpointPath` | string | Infrastructure path (reference only) |
| `durationSeconds` | number | Wall-clock training time |
| `peakVramGb` | number | Peak GPU memory |

**When:** TrainingRun → Completed.

---

### `TrainingRunFailed`

| Field | Type | Description |
|-------|------|-------------|
| `trainingRunId` | string | Run identifier |
| `reason` | string | Error category |

**When:** TrainingRun → Failed.

---

## Evaluation context

### `BenchmarkRunStarted`

| Field | Type | Description |
|-------|------|-------------|
| `benchmarkRunId` | string | Run identifier |
| `checkpointId` | string | Model checkpoint or baseline tag |
| `testSetVersion` | string | HeldOutTestSet version |

**When:** BenchmarkRun Pending → Running.

---

### `BenchmarkRunCompleted`

| Field | Type | Description |
|-------|------|-------------|
| `benchmarkRunId` | string | Run identifier |
| `passAt1` | number | Pass@1 aggregate |
| `passAt5` | number | Pass@5 aggregate (if configured) |
| `avgLatencyMs` | number | Mean inference latency |
| `reportPath` | string | Artifact location |

**When:** BenchmarkRun → Completed.

---

## Reporting context

### `ExperimentReportGenerated`

| Field | Type | Description |
|-------|------|-------------|
| `reportId` | string | Report identifier |
| `comparedMethods` | TrainingMethod[] | Methods in comparison table |
| `comparedLanguages` | TargetLanguage[] | Languages covered |

**When:** Final comparative report is written (Phase 5).
