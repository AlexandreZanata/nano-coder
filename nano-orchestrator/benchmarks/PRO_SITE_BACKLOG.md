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
| S3 | S2 + `stop_grace_s=0.2` + `skip_redundant_stop` + `settle_s=0` | 30.04 s | Site D **26.87 s** | **−3.17 s (−11%)** | **KEEP** |

S2: reuse `llama-server` across consecutive same `model_id` slots.  
S3: shorter post-kill grace; skip extra `stop` when orch already freed the port; zero settle after health.

First S3 attempt orch JSON failed → temporary revert; retry with `orch_bound=5` then KEEP.

---

## D — Ember & Oak Pottery (`pro-site-D-ember-oak`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-cedar-library-pro-archived/` @ 2026-07-21T14:58:49Z |
| Run (UTC) | 2026-07-21T15:01+ (successful orch-bound attempt) |
| Site | Ember & Oak Pottery (craft studio / kiln shop) |
| Schedule | [`large_site_schedule_pro_d.json`](large_site_schedule_pro_d.json) |
| Why this task | New craft domain; measure S3 atop keep-alive |
| Speed | S3 |
| Command | `make nano-large-site-pro-d` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make (orch-bound) | **26.87 s** |
| vs Site C (S2) | **−11%** |
| Orch O0 | 11.78 s |

| Slot | elapsed_s | reused | latency_ms |
|------|-----------|--------|------------|
| styles | 5.80 | no | 3547 |
| home | 2.22 | yes | 2014 |
| menu | 2.24 | yes | 1997 |
| about | 2.20 | yes | 1990 |
| contact | 2.47 | yes | 1986 |

### Results

| Check | Value |
|-------|-------|
| Orch | ok · `orch_bound=5` |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Report | [`runs/large_site_schedule_pro_d.json`](runs/large_site_schedule_pro_d.json) |

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
| Status | **archived** (superseded by D) |
| Archive path | `out/archive/2026-07-21-cedar-library-pro-archived/` |

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
