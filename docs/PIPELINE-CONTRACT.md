# Pipeline Contract — nano-coder

> Phase 1 interface: CLI commands, config schema, and artifact formats. Version all commands from day one (`v1`).

REST API is **out of scope** for phase 1 — see [API-CONTRACT.md](API-CONTRACT.md).

---

## CLI entrypoint

```bash
nano-coder <command> [options]
```

Global flags:

| Flag | Required | Description |
|------|----------|-------------|
| `--config` | No | Path to `pipeline.yaml` (default: `./configs/pipeline.yaml`) |
| `--verbose` | No | Structured logs to stderr |

---

## Commands (v1)

### `seeds import`

Import manual gold seed files.

```bash
nano-coder seeds import --language JavaScript --path ./data/seeds/js/
```

| Option | Required | Description |
|--------|----------|-------------|
| `--language` | Yes | `JavaScript` \| `HTML` \| `FreeMarker` |
| `--path` | Yes | Directory of JSON seed files |

**Seed file schema:**

```json
{
  "id": "seed-js-001",
  "instruction": "Write a function that ...",
  "code": "export function ...",
  "tags": ["array", "utility"]
}
```

**Exit codes:** `0` success | `1` validation error | `2` insufficient seeds (BR-001)

---

### `generate dataset`

Start a `DatasetGenerationRun`.

```bash
nano-coder generate dataset \
  --language JavaScript \
  --target-count 2000 \
  --run-id gen-js-001
```

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--language` | Yes | — | Target language |
| `--target-count` | No | 1500 | Accepted examples goal |
| `--run-id` | Yes | — | Unique run identifier |
| `--max-budget-usd` | No | from config | BR-006 cap |

**Output:** `data/datasets/draft/{run-id}/` (gitignored when large)

---

### `dataset publish`

Publish draft to immutable `DatasetVersion`.

```bash
nano-coder dataset publish --draft-id gen-js-001 --version ds-2026-06-20-js-v1
```

**Preconditions:** BR-005 satisfied, operator confirmation.

---

### `train`

Start a `TrainingRun`.

```bash
nano-coder train \
  --compression-method TTLoRA \
  --data-schedule MixedLanguages \
  --bond-dimension 16 \
  --student-model Qwen2.5-Coder-0.5B \
  --dataset-version ds-2026-06-20-mixed-v1 \
  --run-id train-ttloRA-chi16-001
```

Legacy shorthand (still supported):

```bash
nano-coder train --method LoRA ...
```

| Option | Required | Description |
|--------|----------|-------------|
| `--compression-method` | Yes* | `CompressionMethod` enum — see [TRAINING-METHODS.md](TRAINING-METHODS.md) |
| `--data-schedule` | No | Default `MixedLanguages` |
| `--method` | Yes* | Legacy alias for `--compression-method` |
| `--bond-dimension` | Cond. | Required for tensor methods (`MPO`, `QTHA`, `TTLoRA`, `TRG`, `iPEPS`) |
| `--lora-rank` | Cond. | Required for `LoRA`, `DoRA`, `QLoRA` |
| `--galore-rank` | Cond. | Required for `GaLore` |
| `--decoherence-lambda` | Cond. | Required for `DecoherenceRegularization` |
| `--student-model` | Yes | HuggingFace model id or local path |
| `--dataset-version` | Yes | Published dataset version |
| `--run-id` | Yes | Unique run id |

\* Provide `--compression-method` or `--method`.

---

### `benchmark`

Start a `BenchmarkRun`.

```bash
nano-coder benchmark \
  --checkpoint ./data/checkpoints/train-lora-001 \
  --test-set-version held-out-v1 \
  --run-id bench-001
```

---

### `report export`

Generate comparative report from completed benchmark runs.

```bash
nano-coder report export --run-ids bench-001,bench-002 --output ./reports/final.md
```

---

## Config schema (`pipeline.yaml`)

```yaml
version: v1

teacher:
  provider: anthropic | openai | local
  model: claude-sonnet-4-20250514
  maxBudgetUsd: 200

student:
  defaultModel: Qwen2.5-Coder-0.5B
  quantization: none | 4bit

qualityGates:
  syntaxValidation: true
  lintPass: true
  executionCheck: false
  llmJudge:
    enabled: true
    minScore: 0.7

dataset:
  minExamplesPerLanguage: 1500
  manualReviewSampleRate: 0.05

training:
  defaultCompressionMethod: LoRA
  defaultDataSchedule: MixedLanguages
  loraRank: 16
  bondDimension: 16
  bondDimensionSweep: [4, 8, 16, 32]
  galoreRank: 16
  decoherenceLambda: 0.1
  batchSize: 4
  benchmarkWaves:
    wave1: [FewShot, LoRA, QLoRA, DoRA]
    wave2: [GaLore, TTLoRA, TRG]
    wave3: [MPO, QTHA, LowRankSketching]
    wave4: [iPEPS, DecoherenceRegularization]

benchmark:
  passAtK: [1, 5]
  heldOutTestSetVersion: held-out-v1

security:
  sandboxExecution: true
  secretsFromEnv: true
```

---

## Error format (CLI)

Structured JSON on stderr when `--json-errors` is set:

```json
{
  "error": {
    "code": "SEED_COUNT_INSUFFICIENT",
    "message": "At least 50 gold seeds required for JavaScript",
    "correlationId": "uuid"
  }
}
```

| Code | HTTP mapping (future) | Meaning |
|------|----------------------|---------|
| `SEED_COUNT_INSUFFICIENT` | 400 | BR-001 |
| `HELD_OUT_LEAK_DETECTED` | 409 | BR-004 |
| `BUDGET_EXCEEDED` | 402 | BR-006 |
| `DATASET_NOT_PUBLISHED` | 412 | BR-007 |
| `TEST_SET_VERSION_MISMATCH` | 409 | BR-008 |

---

## Artifact formats

| Artifact | Format | Location |
|----------|--------|----------|
| Published dataset | JSONL (one example per line) | `data/datasets/{version}/` |
| Checkpoint | HF format | `data/checkpoints/{run-id}/` |
| Benchmark results | JSON + Markdown summary | `data/benchmarks/{run-id}/` |
| Event log | JSONL append-only | `data/events/events.jsonl` |

---

## Environment variables

See [.env.example](../.env.example). Required for Infrastructure:

| Variable | Purpose |
|----------|---------|
| `TEACHER_API_KEY` | Teacher LLM API (never commit) |
| `HF_TOKEN` | HuggingFace model download (optional) |
| `NANO_CODER_DATA_DIR` | Override default `data/` root |
