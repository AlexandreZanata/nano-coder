# Business Rules — nano-coder

> Named rules in GIVEN/WHEN/THEN format. Test in Domain layer before implementation.

---

## BR-001 — Gold seed minimum before expansion

```
GIVEN a DatasetGenerationRun is requested
WHEN the count of GoldSeedExample records for the target TargetLanguage is less than 50
THEN the run MUST NOT start
AND a domain error SeedCountInsufficient MUST be raised
```

---

## BR-002 — Quality gate mandatory for synthetic examples

```
GIVEN a SyntheticExample is produced by the TeacherModel
WHEN no QualityGate has accepted the example
THEN the example MUST NOT be added to a SyntheticDataset
AND ExampleRejected MUST be recorded
```

---

## BR-003 — Syntax validation per language

```
GIVEN a SyntheticExample with TargetLanguage JavaScript
WHEN SyntaxValidation gate runs
THEN the code MUST parse with a configured JS parser AND pass configured lint rules

GIVEN TargetLanguage HTML
WHEN SyntaxValidation gate runs
THEN the markup MUST parse as valid HTML5 (or project-defined subset)

GIVEN TargetLanguage FreeMarker
WHEN SyntaxValidation gate runs
THEN the template MUST pass FreeMarker syntax validation
```

---

## BR-004 — Held-out set isolation

```
GIVEN an example belongs to HeldOutTestSet
WHEN any DatasetGenerationRun or TrainingRun executes
THEN that example MUST NOT appear in training or synthetic generation inputs
AND violation MUST abort the run with HeldOutLeakDetected
```

---

## BR-005 — Dataset publish thresholds

```
GIVEN a SyntheticDataset for one TargetLanguage
WHEN the operator requests publish
THEN the dataset MUST contain at least 1,500 accepted SyntheticExample records
AND at least 90% MUST have passed SyntaxValidation
AND a manual review sample of at least 5% MUST be marked accepted by PipelineOperator
AND DatasetPublished MUST be emitted with a new DatasetVersion
```

*Note: thresholds are configurable; defaults above match project target (~1.5k–3k per language).*

---

## BR-006 — Teacher spend guardrail

```
GIVEN a DatasetGenerationRun is active
WHEN cumulative TeacherModel API cost exceeds configured maxBudgetUsd
THEN generation MUST stop gracefully
AND the run transitions to Failed with reason BudgetExceeded
AND partial results MUST NOT be auto-published
```

---

## BR-007 — Human confirm before training

```
GIVEN a TrainingRun is requested
WHEN the linked SyntheticDataset is not in Published state
THEN TrainingRun MUST NOT start
AND HumanConfirmRequired MUST be surfaced to PipelineOperator
```

---

## BR-008 — Benchmark requires frozen test set

```
GIVEN a BenchmarkRun is requested
WHEN HeldOutTestSet version differs from the version recorded in experiment config
THEN BenchmarkRun MUST NOT start
AND TestSetVersionMismatch MUST be raised
```

---

## BR-009 — No auto-execution of generated code on operator machine without sandbox

```
GIVEN CorrectnessCheck includes ExecutionCheck
WHEN generated code is executed
THEN it MUST run inside an isolated sandbox (container or restricted subprocess)
AND network access MUST be disabled by default
```

*Aligns with ASI05 — Unexpected Code Execution.*

---

## BR-010 — LLM-as-judge is advisory only

```
GIVEN LLMJudge QualityGate scores a SyntheticExample
WHEN score is below threshold
THEN the example is rejected for dataset inclusion
AND the judge score MUST NOT be the sole acceptance criterion (SyntaxValidation still required)
```

---

## BR-011 — Incremental vs mixed training experiment isolation

```
GIVEN TrainingMethod is IncrementalByLanguage
WHEN training completes for one TargetLanguage
THEN checkpoint MUST be tagged with language and prior DatasetVersion
AND BenchmarkRun for other languages MUST use the correct language-specific checkpoint
```

---

## BR-012 — Report comparability

```
GIVEN two BenchmarkRun results are compared in the final report
WHEN TrainingMethod, StudentModel, DatasetVersion, or HeldOutTestSet version differ in undocumented ways
THEN those runs MUST NOT appear in the same comparison table without explicit footnote
```

---

## BR-013 — Evidence level on every training run

```
GIVEN a TrainingRun completes for any CompressionMethod
WHEN BenchmarkRun artifacts or reports are written
THEN each run MUST record EvidenceLevel (Established | QuantumInspired | NovelApplication | Speculative)
AND tensor-network runs MUST record BondDimension (χ)
AND L4 Speculative runs (DecoherenceRegularization) MUST be labeled in report title and tables
AND agents MUST NOT describe L2 methods as "novel physics" — only as quantum-inspired classical simulation
```

---

## BR-014 — Matched parameter budget comparison

```
GIVEN two CompressionMethod runs are compared as "better/worse"
WHEN trainable parameter counts differ by more than 10%
THEN comparison MUST include a footnote or a matched-param companion run
AND BondDimension χ and loraRank MUST NOT be equated without explicit param-count mapping
```
