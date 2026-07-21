# Large-site multi-model test schedule

> Operator schedule for monitoring **every bake-off worker + orchestrator** while building one large site.  
> Cap: **≤5 MicroTasks** (ASI08). Orchestrator unload between slots (peak VRAM ≤6000 MB).

## Goal

Build a **large coffee-shop site** (multi-page HTML + JS cart helpers + FreeMarker menu partial) by:

1. Running **orchestrator** (`smollm3-3b`) to propose a MicroTask JSON plan  
2. Executing a **canonical 5-slot schedule** — **one model per task** — so each worker is loaded, measured, and judged  

## Models under monitor (live all-models schedule)

Canonical file: [`large_site_schedule_all_models.json`](large_site_schedule_all_models.json) — **one unique model per task**.

| Slot | Model ID | Role | Site piece |
|------|----------|------|------------|
| O0 | `smollm3-3b` | orchestrator | Decompose → bind 5 MicroTasks |
| W1 | `qwen25-coder-0.5b-html-ft` | worker | `home.html` |
| W2 | `qwen25-coder-0.5b` | worker | `menu.html` + prices |
| W3 | `qwen25-coder-0.5b-javascript-ft` | worker | `cart.js` |
| W4 | `gemma3-270m` | worker | `formatMoney.js` |
| W5 | `qwen25-coder-0.5b-freemarker-ft` | worker | `menu-item.ftl` |

```bash
make nano-large-site-all
```

### Measured 2026-07-21 — GREEN (live orch)

- Orch: **OK** (`count=5`, `orch_bound=5`)
- Workers: **5/5** judge + quality
- Peak VRAM: **3547 MB** (orch) · report: `benchmarks/runs/large_site_schedule_all_models.json`
- Proposal: `out/proposal/`

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

## All-models schedule (unique worker per slot + live orch)

See [`large_site_schedule_all_models.json`](large_site_schedule_all_models.json):

| Slot | Model | Piece |
|------|-------|-------|
| O0 | `smollm3-3b` | decompose → bind plan to slots |
| W1 | `qwen25-coder-0.5b` | home.html |
| W2 | `gemma3-270m` | menu.html |
| W3 | `qwen3-0.6b` | cart.js |
| W4 | `smollm2-360m` | formatMoney.js |
| W5 | `qwen25-coder-0.5b-freemarker-ft` | menu-item.ftl |

```bash
make nano-large-site-all
# or:
NANO_ORCH_HTML_VALIDATE=1 python benchmarks/run_large_site_schedule.py \
  --schedule benchmarks/large_site_schedule_all_models.json
```

Orch binds MicroTasks by id/language onto the unique model roster (`orch_bind` in the JSON report). If orch JSON fails, canonical slot prompts still run (one model each).


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

## Pro-site CSS+HTML series (orchestrator-only results)

Canonical backlog: [`PRO_SITE_BACKLOG.md`](PRO_SITE_BACKLOG.md).

| ID | Site | Make target | Wall (latest) | Notes |
|----|------|-------------|---------------|-------|
| A | Harbor Coffee | `make nano-large-site-pro` | — | archived |
| B | Summit Trail | `make nano-large-site-pro-b` | 53.31 s | cold start/stop baseline |
| C | Cedar Civic Library | `make nano-large-site-pro-c` | 30.04 s | S2 keep-alive (−44% vs B) |
| D | Ember & Oak Pottery | `make nano-large-site-pro-d` | **26.87 s** | S3 stop_grace (−11% vs C) |
| E | Solstice Yoga Collective | `make nano-large-site-pro-e` | 32.02 s | S4 warm REVERT; final under S3 |
| F | Fern & Field Botanicals | `make nano-large-site-pro-f` | 17.19 s | S5 skip-orch (−36% vs D); archived |
| G | Beacon Dental Care | `make nano-large-site-pro-g` | 13.00 s | S6 skip-dup-kill (−24% vs F); archived |
| H | Atlas Climbing Gym | `make nano-large-site-pro-h` | 11.43 s | S7 CTX=2048 + trust health (−12% vs G); archived |
| I | Lumen Photo Studio | `make nano-large-site-pro-i` | **9.82 s** | S8 temp0 + tighter tokens (−14% vs H); archived |
| J | Copper Lantern Bookstore | `make nano-large-site-pro-j` | 10.07 s | S9 REVERT; final under S8; archived |
| K | Willow & Whisk Bakery | `make nano-large-site-pro-k` | 10.02 s | S10 REVERT; final under S8; archived |
| L | Moss & Stone Garden | `make nano-large-site-pro-l` | 10.01 s | S11 REVERT; final under S8; archived |
| M | Bright Harbor Marina | `make nano-large-site-pro-m` | 5.96 s | S12 parallel HTML (−39% vs I); archived |
| N | Northline Bike Co-op | `make nano-large-site-pro-n` | **4.83 s** | S13 all-slots parallel (−19% vs M); archived |
| O | Marble & Rye Deli | `make nano-large-site-pro-o` | 4.98 s | S14 REVERT (CSS truncate); final under S13 |

Speed: S2–S8 + S12/S13 parallel kept · S4/S9/S10/S11/S14 REVERT. Best wall Site N **4.83 s**. CLI: `--keep-alive` / `--no-keep-alive` / `--skip-orchestrator`.

**Rule:** never hand-edit `out/proposal/` site files; archive before each new site run.
