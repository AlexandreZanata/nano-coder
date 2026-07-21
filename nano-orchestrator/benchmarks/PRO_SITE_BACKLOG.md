# Pro-site benchmark backlog (orchestrator-only results)

> Rule: **never hand-edit** `out/proposal/` site files. Archive prior proposals before each new run.
> Operator harness (schedules, Arena, docs) may change; **result HTML/CSS must come only from nano-orchestrator workers**.

## Protocol

1. Archive `out/proposal/` → `out/archive/<date>-<site>-archived/`
2. Clear `out/proposal/`
3. Run schedule via `make nano-large-site-pro*` (no post-run file edits)
4. Record wall-clock, orch bind, pass bar, openable pages, peak VRAM
5. Append entry here + touch `PROGRESS.yaml`
6. Speed experiments: measure vs prior baseline; **KEEP** if faster + green, else **REVERT** code

---

## Speed experiments

| ID | Approach | Baseline | Measured | Delta | Decision |
|----|----------|----------|----------|-------|----------|
| S1 | Cold start/stop every worker slot | — | Site B **53.31 s** | — | prior default |
| S2 | `keep_alive_same_model` + settle 0.15s | 53.31 s | Site C **30.04 s** | **−23.27 s (−44%)** | **KEEP** |

S2 details: reuse `llama-server` across consecutive slots with the same `model_id` (pro schedules use one HTML-FT worker for all 5 files). Flags: schedule `speed.keep_alive_same_model` or CLI `--keep-alive` / `--no-keep-alive`.

---

## C — Cedar Civic Library (`pro-site-C-cedar-library`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-summit-trail-pro-archived/` @ 2026-07-21T14:49:12Z |
| Run start (UTC) | 2026-07-21T14:50:56Z |
| Site | Cedar Civic Library (civic / fees catalog) |
| Schedule | [`large_site_schedule_pro_c.json`](large_site_schedule_pro_c.json) |
| Why this task | New domain (library vs outdoor/coffee); stress same CSS+4 HTML shape; first measured keep-alive run |
| Speed | S2 keep-alive enabled |
| Command | `make nano-large-site-pro-c` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **30.04 s** |
| vs Site B baseline | **−44%** |

| Slot | Role | elapsed_s | reused | kept_alive |
|------|------|-----------|--------|------------|
| O0 | orch | ~13 s (in wall) | — | — |
| W1 styles | css | 6.96 | no | yes |
| W2 home | html | 2.21 | yes | yes |
| W3 menu | html | 2.20 | yes | yes |
| W4 about | html | 2.19 | yes | yes |
| W5 contact | html | 3.26 | yes | no (final stop) |

`slots_reused=4` · `slots_kept_alive=4` · peak VRAM **~1579 MB** workers

### Results

| Check | Value |
|-------|-------|
| Orch | ok · `orch_bound=5` |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Report | [`runs/large_site_schedule_pro_c.json`](runs/large_site_schedule_pro_c.json) |
| Preview | http://127.0.0.1:8765/site/index.html |

---

## B — Summit Trail Outfitters (`pro-site-B-summit-trail`)

| Field | Value |
|-------|-------|
| Started (UTC) | 2026-07-21T14:42:51Z (archive) · run 2026-07-21T14:44:16Z |
| Ended (UTC) | 2026-07-21T14:45:09Z |
| Site | Summit Trail Outfitters (outdoor gear shop) |
| Schedule | [`large_site_schedule_pro_b.json`](large_site_schedule_pro_b.json) |
| Why this task | New domain vs Harbor Coffee; same shape (CSS + 4 HTML) for comparable quality/latency |
| Prior archive | `out/archive/2026-07-21-harbor-coffee-pro-archived/` |
| Command | `make nano-large-site-pro-b` |
| Wall clock | **53.31 s** (cold start/stop — baseline for S2) |
| Status | **archived** (superseded by C) |
| Archive | `out/archive/2026-07-21-summit-trail-pro-archived/` |

---

## A — Harbor Coffee Co. (`pro-site-A-harbor`)

| Field | Value |
|-------|-------|
| Site | Harbor Coffee Co. |
| Schedule | [`large_site_schedule_pro.json`](large_site_schedule_pro.json) |
| Result | 5/5 workers, 4/4 openable, CSS linked; Arena `/site/` preview |
| Archive | `out/archive/2026-07-21-harbor-coffee-pro-archived/` |
| Status | **archived** |
