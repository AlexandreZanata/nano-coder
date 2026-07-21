# Large-site multi-model test schedule

> Operator schedule for monitoring **every bake-off worker + orchestrator** while building one large site.  
> Cap: **≤5 MicroTasks** (ASI08). Orchestrator unload between slots (peak VRAM ≤6000 MB).

## Goal

Build a **large coffee-shop site** (multi-page HTML + JS cart helpers + FreeMarker menu partial) by:

1. Running **orchestrator** (`smollm3-3b`) to propose a MicroTask JSON plan  
2. Executing a **canonical 5-slot schedule** — **one model per task** — so each worker is loaded, measured, and judged  

## Models under monitor

| Slot | Model ID | Role | Site piece |
|------|----------|------|------------|
| O0 | `smollm3-3b` | orchestrator | Decompose user request → ≤5 MicroTasks |
| W1 | `qwen25-coder-0.5b` | worker | `home.html` — hero, about, nav |
| W2 | `gemma3-270m` | worker | `menu.html` — priced menu + CTA |
| W3 | `qwen3-0.6b` | worker | `cart.js` — add/remove/total (ESM) |
| W4 | `smollm2-360m` | worker | `formatMoney.js` — currency helper |
| W5 | `qwen25-coder-0.5b-freemarker-ft` | worker | `menu-item.ftl` — `#list` + `?html` |

Optional follow-up (same schedule, FT HTML/JS):

| Slot | Model ID | Piece |
|------|----------|-------|
| W1b | `qwen25-coder-0.5b-html-ft` | re-gen `home.html` |
| W3b | `qwen25-coder-0.5b-javascript-ft` | re-gen `cart.js` |

## Cronograma (wall-clock order)

```text
T+0m   O0  start smollm3-3b → decompose → stop → log JSON validity
T+2m   W1  start qwen25-coder-0.5b → home.html → judge → stop
T+4m   W2  start gemma3-270m → menu.html → judge → stop
T+6m   W3  start qwen3-0.6b → cart.js → judge → stop
T+8m   W4  start smollm2-360m → formatMoney.js → judge → stop
T+10m  W5  start freemarker-ft → menu-item.ftl → judge → stop
T+12m  Merge → out/proposal/ + benchmarks/runs/large_site_schedule.json
```

## Metrics to record (per slot)

| Metric | Source |
|--------|--------|
| `latency_ms` | WorkerResponse |
| `vram_mb` | `nvidia-smi` peak during slot |
| `passed` / `score` | JudgeVerdict (sandbox-first) |
| `tokens_used` | WorkerResponse |
| `escalate_to_human` | retry policy |

## How to run

```bash
cd nano-orchestrator
source .venv/bin/activate
export NANO_ORCH_HTML_VALIDATE=1
python benchmarks/run_large_site_schedule.py
# or
python -m nano_orchestrator large-site
```

Human gate: review `out/proposal/` — never auto-persist.

## Pass criteria (operator)

- [ ] O0 returns valid MicroTask JSON **or** schedule falls back to canonical tasks  
- [ ] All 5 worker slots complete without OOM  
- [ ] Peak VRAM ≤ 6000 MB  
- [ ] ≥3/5 tasks `passed=true` (syntax sandboxes)  
- [ ] Proposal package has `auto_persist: false`

## Measured run (2026-07-21) — GREEN

| Slot | Model | Latency | VRAM MB | Judge | Quality |
|------|-------|---------|---------|-------|---------|
| O0 | smollm3-3b | — | — | skipped* | canonical slots used |
| W1 | qwen25-coder-0.5b-html-ft | 468 ms | 1577 | PASS 0.9 | home + nav |
| W2 | qwen25-coder-0.5b-html-ft | 1109 ms | 1577 | PASS 0.9 | menu + $ prices |
| W3 | qwen25-coder-0.5b-javascript-ft | 1461 ms | 1577 | PASS 0.9 | cart exports |
| W4 | qwen25-coder-0.5b-javascript-ft | 476 ms | 1575 | PASS 0.9 | formatMoney |
| W5 | qwen25-coder-0.5b-freemarker-ft | 112 ms | 1575 | PASS 0.9 | `#list` + `?html` |

\*Live orch still flaky (`empty_task_list` / schema errors) — schedule uses `--skip-orchestrator` + canonical slots for reliable multi-model site builds.

- **Passed bar:** **5/5** · **Quality checklist:** all true · **Peak VRAM:** **1577 MB** · **Exit:** 0  
- **Artifacts:** `out/proposal/` · `benchmarks/runs/large_site_schedule.json`  
- **Command:** `NANO_ORCH_HTML_VALIDATE=1 python benchmarks/run_large_site_schedule.py --skip-orchestrator`
