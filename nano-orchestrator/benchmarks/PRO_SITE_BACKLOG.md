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
| S4 | Warm worker on `:8082` during orch (parallel load) | 26.87 s | 27.31 / 31.23 / 32.70 s | not faster | **REVERT** |
| S5 | `speed.skip_orchestrator` + S3 keep-alive (canonical slots) | 26.87 s | Site F **17.19 s** | **−9.68 s (−36%)** | **KEEP** |
| S6 | Skip duplicate shell port-kill + `HEALTH_SLEEP=0.2` + tighter `max_tokens` | 17.19 s | Site G **13.00 s** | **−4.19 s (−24%)** | **KEEP** |
| S7 | `CTX=2048` + `trust_start_health` (skip Python re-poll after shell OK) | 13.00 s | Site H **11.43 s** | **−1.57 s (−12%)** | **KEEP** |
| S8 | `temperature=0` + `stop_grace_s=0` + tighter tokens (750/480) | 11.43 s | Site I **9.82 s** | **−1.61 s (−14%)** | **KEEP** |

S2: reuse `llama-server` across consecutive same `model_id` slots.  
S3: shorter post-kill grace; skip extra `stop` when orch already freed the port; zero settle after health.  
S4: overlapped worker GGUF load with orch decompose (dual-port). Warm OK but wall ≥ baseline → code restored to S3.  
S5: skip live orch decompose when schedule already has canonical CSS/HTML slots; workers still generate all files via nano-orchestrator. Use when speed matters more than orch-bind telemetry.  
S6: `SKIP_PRE_KILL=1` from Python `start_server` (no second `fuser`+sleep in shell); faster health poll; styles `max_tokens` 900 / HTML 560 (was 1200/700).  
S7: worker `CTX=2048` (vs default 8192) + trust shell `/health` success (no second Python poll loop). Peak VRAM also dropped (~1503 MB).  
S8: greedy decode (`temperature=0`), zero stop grace, styles/HTML `max_tokens` 750/480 (was 900/560).

First S3 attempt orch JSON failed → temporary revert; retry with `orch_bound=5` then KEEP.

---

## I — Lumen Photo Studio (`pro-site-I-lumen-photo`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-atlas-climbing-pro-archived/` @ 2026-07-21T15:27:20Z |
| Site | Lumen Photo Studio (creative services / packages) |
| Schedule | [`large_site_schedule_pro_i.json`](large_site_schedule_pro_i.json) |
| Why this task | New creative-services domain; measure **S8** vs H **11.43 s** |
| Speed | **S8** (on top of S5–S7) |
| Command | `make nano-large-site-pro-i` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **9.82 s** |
| vs Site H S7 baseline | **−14%** |
| Orch O0 | skipped |

| Slot | elapsed_s | reused |
|------|-----------|--------|
| styles | 3.26 | no |
| home | 1.57 | yes |
| menu | 1.57 | yes |
| about | 1.58 | yes |
| contact | 1.67 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1503 MB** |
| Report | [`runs/large_site_schedule_pro_i.json`](runs/large_site_schedule_pro_i.json) |

---

## H — Atlas Climbing Gym (`pro-site-H-atlas-climbing`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-beacon-dental-pro-archived/` @ 2026-07-21T15:22:52Z |
| Site | Atlas Climbing Gym (recreation / day passes) |
| Schedule | [`large_site_schedule_pro_h.json`](large_site_schedule_pro_h.json) |
| Why this task | New recreation domain; measure **S7** vs G **13.00 s** |
| Speed | **S7** (on top of S5/S6) |
| Command | `make nano-large-site-pro-h` |
| Status | **archived** (superseded by I) |
| Archive path | `out/archive/2026-07-21-atlas-climbing-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **11.43 s** |
| vs Site G S6 baseline | **−12%** |
| Orch O0 | skipped |

| Slot | elapsed_s | reused |
|------|-----------|--------|
| styles | 3.84 | no |
| home | 1.82 | yes |
| menu | 1.79 | yes |
| about | 1.79 | yes |
| contact | 2.03 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1503 MB** |
| Report | [`runs/large_site_schedule_pro_h.json`](runs/large_site_schedule_pro_h.json) |

---

## G — Beacon Dental Care (`pro-site-G-beacon-dental`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-fern-field-pro-archived/` @ 2026-07-21T15:19:11Z |
| Site | Beacon Dental Care (clinic / services + fees) |
| Schedule | [`large_site_schedule_pro_g.json`](large_site_schedule_pro_g.json) |
| Why this task | New healthcare domain; measure **S6** vs F **17.19 s** |
| Speed | **S6** (on top of S5 keep-alive + skip-orch) |
| Command | `make nano-large-site-pro-g` |
| Status | **archived** (superseded by H) |
| Archive path | `out/archive/2026-07-21-beacon-dental-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **13.00 s** |
| vs Site F S5 baseline | **−24%** |
| Orch O0 | skipped |

| Slot | elapsed_s | reused |
|------|-----------|--------|
| styles | 3.81 | no |
| home | 1.81 | yes |
| menu | 1.79 | yes |
| about | 3.38 | yes (2 attempts) |
| contact | 2.03 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5/S6) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1581 MB** |
| Report | [`runs/large_site_schedule_pro_g.json`](runs/large_site_schedule_pro_g.json) |

---

## F — Fern & Field Botanicals (`pro-site-F-fern-field`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-solstice-yoga-pro-archived/` @ 2026-07-21T15:14:58Z |
| Site | Fern & Field Botanicals (plant shop) |
| Schedule | [`large_site_schedule_pro_f.json`](large_site_schedule_pro_f.json) |
| Why this task | New retail/plants domain; measure S5 skip-orch speed mode |
| Speed | **S5** (skip orch + S3 keep-alive) |
| Command | `make nano-large-site-pro-f` |
| Status | **archived** (superseded by G) |
| Archive path | `out/archive/2026-07-21-fern-field-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **17.19 s** |
| vs Site D S3 baseline | **−36%** |
| Orch O0 | skipped |

| Slot | elapsed_s | reused |
|------|-----------|--------|
| styles | 5.95 | no |
| home | 2.21 | yes |
| menu | 2.21 | yes |
| about | 4.18 | yes |
| contact | 2.47 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Report | [`runs/large_site_schedule_pro_f.json`](runs/large_site_schedule_pro_f.json) |

---

## E — Solstice Yoga Collective (`pro-site-E-solstice-yoga`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-ember-oak-pro-archived/` @ 2026-07-21T15:04:06Z |
| Site | Solstice Yoga Collective (studio / class drop-ins) |
| Schedule | [`large_site_schedule_pro_e.json`](large_site_schedule_pro_e.json) |
| Why this task | New wellness domain; measure S4 warm-during-orch vs S3 |
| Speed | S4 **REVERT**; Site E final timed under **S3** |
| Command | `make nano-large-site-pro-e` |
| Status | **archived** (superseded by F) |
| Archive path | `out/archive/2026-07-21-solstice-yoga-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| S4 attempts (reverted) | 27.31 / 31.23 / 32.70 s |
| Final S3 make (orch-bound) | **32.02 s** |
| Orch O0 (S3 final) | 11.67 s |

### Results

| Check | Value |
|-------|-------|
| Orch | ok · `orch_bound=5` |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Report | [`runs/large_site_schedule_pro_e.json`](runs/large_site_schedule_pro_e.json) |

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
| Status | **archived** (superseded by E) |
| Archive path | `out/archive/2026-07-21-ember-oak-pro-archived/` |

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
