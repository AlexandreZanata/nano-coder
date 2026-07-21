# Negative result — Nano-Orchestrator vs solo 0.5B

**Date:** 2026-07-21  
**Decision:** **keep solo `Qwen2.5-Coder-0.5B`** — do not stack further orchestration features for the MVP success criterion.

**Raw run:** [`benchmarks/runs/success_gates.json`](../benchmarks/runs/success_gates.json)  
**Runner:** `python benchmarks/run_success_gates.py`

## GATE-001 (failed)

Same 30 MicroTasks from `tests/golden/gold_set.json`, Judge/sandbox Pass@1:

| Mode | Overall Pass@1 | Passed / Total |
|------|----------------|----------------|
| Solo `qwen25-coder-0.5b` | **0.8667** | 26 / 30 |
| Orchestration (Phase 5 routing + Judge + retries) | **0.7333** | 22 / 30 |

### Per language

| Language | Solo Pass@1 | Orch Pass@1 | Orch worker (config) |
|----------|-------------|-------------|----------------------|
| javascript | 0.90 (9/10) | 0.50 (5/10) | `qwen25-coder-0.5b-javascript-ft` |
| html | 0.80 (8/10) | 1.00 (10/10) | `qwen25-coder-0.5b-html-ft` |
| freemarker | 0.90 (9/10) | 0.70 (7/10) | `qwen25-coder-0.5b-freemarker-ft` |

**Observation:** HTML FT helped; **JS FT smoke regresses hard** vs base solo (0.50 vs 0.90). That alone sinks overall orchestration below solo.

## GATE-002 / GATE-003 (passed)

| Gate | Result | Detail |
|------|--------|--------|
| GATE-002 peak VRAM ≤ 6000 MB | **PASS** | 1577 MB |
| GATE-003 p50 ≤ 2000 ms | **PASS** | 323 ms (Phase-1 target) |

VRAM and latency gates do **not** override the Pass@1 kill criterion.

## Decision (GATE-NEG)

Per README §0 and ADR draft:

> If orchestration fails this bar → **keep solo 0.5B**. Do not add complexity.

**Ship / research conclusion:** prefer **solo Qwen2.5-Coder-0.5B** as the coding worker for gold-set micro-tasks. Orchestration scaffolding remains useful as instrumentation, but it is **not** justified as the default quality path until specialized workers beat solo on gold (especially JS).

Optional follow-ups (out of MVP scope unless reopened):

1. Retrain JS worker with stronger data / more steps; re-run gates.  
2. Set `prefer_fine_tuned: false` in `config/worker_routing.json` and re-measure (base routing only).  
3. Keep HTML FT if a future gate reopens with language-weighted metrics.
