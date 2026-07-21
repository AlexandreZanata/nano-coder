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
| S9 | `top_k=1` + `skip_final_stop` (leave server up after last slot) | 9.82 s | **9.60 s** but quality fail | −0.22 s / red | **REVERT** |
| S10 | `log_calls=false` + `cache_prompt=true` | 9.82 s | **10.43 s** (green) | +0.61 s | **REVERT** |
| S11 | Parallel HTML slots + llama `-np 4` | 9.82 s | **3.05 s** but 0/5 red | red | **REVERT** |
| S12 | Parallel HTML + `CTX=8192` + `-np 4` | 9.82 s | Site M **5.96 s** | **−3.86 s (−39%)** | **KEEP** |
| S13 | All 5 slots parallel + `CTX=10240` + `-np 5` | 5.96 s | Site N **4.83 s** | **−1.13 s (−19%)** | **KEEP** |
| S14 | S13 + tokens 700/440 + `skip_final_stop` | 4.83 s | **5.00 s** red quality | slower / red | **REVERT** |
| S15 | S13 + `-fa on` + `-kvu` (unified KV) | 4.83 s | **4.83 s** green (tie) | 0.00 s | **REVERT** |
| S16 | S13 + `-b 4096` + `-ub 1024` (larger prefill batch) | 4.83 s | **4.80 s** green (noise) | −0.03 s | **REVERT** |
| S17 | styles `max_tokens=750` + `health_sleep=0.1` + `skip_final_stop` | 4.83 s | **4.57 s** red (`styles_has_form`) | faster / red | **REVERT** |
| S18 | Early-stop `<<<END>>>` stop marker (avoid padding to max_tokens) | 4.83 s | **2.00 s** red (0/5 echo/stop) | faster / red | **REVERT** |
| S19 | S13 + `CTX=9216` (smaller KV vs 10240, keep `-np 5`) | 4.83 s | **4.81 s** green (noise) | −0.02 s | **REVERT** |
| S20 | Compact CSS (form early) + styles `max_tokens=720` | 4.83 s | **4.56 s** red (`styles_has_footer`) | faster / red | **REVERT** |
| S21 | Ultra-compact CSS (footer+form early) + styles `max_tokens=700` | 4.83 s | **6.26 s** red (menu judge 4/5; styles CSS OK) | slower / red | **REVERT** |
| S22 | Retry styles `max_tokens=700` + early footer/form (booking track) | 4.83 s | **6.47 s** green | +1.64 s | **REVERT** |

S2: reuse `llama-server` across consecutive same `model_id` slots.  
S3: shorter post-kill grace; skip extra `stop` when orch already freed the port; zero settle after health.  
S4: overlapped worker GGUF load with orch decompose (dual-port). Warm OK but wall ≥ baseline → code restored to S3.  
S5: skip live orch decompose when schedule already has canonical CSS/HTML slots; workers still generate all files via nano-orchestrator. Use when speed matters more than orch-bind telemetry.  
S6: `SKIP_PRE_KILL=1` from Python `start_server` (no second `fuser`+sleep in shell); faster health poll; styles `max_tokens` 900 / HTML 560 (was 1200/700).  
S7: worker `CTX=2048` (vs default 8192) + trust shell `/health` success (no second Python poll loop). Peak VRAM also dropped (~1503 MB).  
S8: greedy decode (`temperature=0`), zero stop grace, styles/HTML `max_tokens` 750/480 (was 900/560).  
S9: `top_k=1` + skip final server stop. Wall slightly faster but `styles_has_form=false` → pass bar failed → code restored to S8.  
S10: disable LLM call logging + llama.cpp `cache_prompt`. Green but slower than S8 best → code restored to S8.  
S11: ThreadPoolExecutor for HTML slots with `-np 4` at CTX 2048. Styles HTTP 400 (ctx split too small) → REVERT.  
S12: same parallel path with `CTX=8192` so each `-np` slot has enough context; styles sequential then 4 HTML concurrent.  
S13: cold-start once then run **all** slots (CSS+HTML) concurrently with `CTX=10240` / `-np 5`. **Best kept wall.**  
S14: tighter CSS/HTML tokens + skip final stop. Truncated CSS (`styles_has_footer/form=false`) and slower wall → REVERT to S13.
S15: force Flash Attention on + unified KV (`-kvu`) with `-np 5`. Green but wall tied N **4.83 s** (no speedup) → REVERT harness; Site P final under S13.
S16: larger `-b 4096` / `-ub 1024` for multi-slot prefill. Green **4.80 s** but within noise of S13 (~4.8 s) → REVERT; Site Q final under S13.
S17: styles `max_tokens=750` + `health_sleep=0.1` + `skip_final_stop`. Faster wall but CSS truncated before form rules → REVERT; Site R final under S13.
S18: `stop_extra=["<<<END>>>"]` in prompts. Model echoed meta-instructions and stopped at ~30 tokens (0/5) → REVERT; Site S final under S13.
S19: `CTX=9216` with `-np 5`. Green **4.81 s** but within noise of S13 (~4.8 s) → REVERT to CTX 10240; Site T final under S13.
S20: compact CSS + styles `max_tokens=720`. Faster but truncated before `.site-footer` → REVERT; Site U final under S13 (780).
S21: ultra-compact CSS with footer+form early + `max_tokens=700`. Styles quality green (footer+form present) but menu judge failed (4/5) and wall slower → REVERT tokens to 780; Site V final under S13. Note: host `:8081` was occupied by docker-proxy — measured on `:8082`.
S22: retry styles `max_tokens=700` early footer/form on Harborline. **Green** pass bar (styles footer+form OK) but wall **6.47 s** vs S13 best **4.83 s** (cold-start/env slower this session) → REVERT tokens to 780; keep early-footer CSS layout.

### Lovable direction (project-type expansion)

**North-star:** a chat that turns plain text into a complete professional system (sites first → apps later) — the next Lovable: extremely fast, beautiful, orchestrator-built.

| Track | Site kinds | Status |
|-------|------------|--------|
| Retail / local biz | A–T | done series |
| SaaS landing | U Brightfolio | archived |
| Portfolio / agency | V Fieldwork Studio | archived |
| Booking / services | **W Harborline Escape** | done |
| Chat → full system | planned | text prompt → orch decompose → workers (no hand edits) |

Invariant: **result HTML/CSS only from workers** — no hand edits to `out/proposal/`.  
Speed ceiling today: **S13 ~4.8 s** (best kept). S22 proved styles700 can stay green with early footer/form, but wall must beat 4.83 before KEEP.

First S3 attempt orch JSON failed → temporary revert; retry with `orch_bound=5` then KEEP.

---

## W — Harborline Escape Rooms (`pro-site-W-harborline-escape`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-fieldwork-agency-pro-archived/` @ 2026-07-21T16:58:00Z |
| Site | Harborline Escape Rooms (booking / services + room rates) |
| Schedule | [`large_site_schedule_pro_w.json`](large_site_schedule_pro_w.json) |
| Why this task | **Booking Lovable track**; measure **S22** styles700 retry |
| Speed | S22 **REVERT** (green but slower wall); Site W final under **S13** on `:8082` |
| Command | `NANO_PORT=8082 make nano-large-site-pro-w` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S22 attempt (green, slow) | **6.47 s** — styles tok=700 OK; archived `out/archive/2026-07-21-harborline-s22-slow/` |
| Final make (S13 @8082) | **6.75 s** (env slower vs historical 4.8 s) |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.62 | yes |
| home | 2.95 | yes |
| menu | 2.94 | yes |
| about | 2.99 | yes |
| contact | 2.94 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~656 MB (smi sample; parallel load)
- Report: [`runs/large_site_schedule_pro_w.json`](runs/large_site_schedule_pro_w.json)

### Notes

- No hand edits to `out/proposal/`
- Booking track complete in Lovable expansion table

---

## V — Fieldwork Studio (`pro-site-V-fieldwork-agency`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-brightfolio-saas-pro-archived/` @ 2026-07-21T16:50:21Z |
| Site | Fieldwork Studio (design agency / portfolio + services board) |
| Schedule | [`large_site_schedule_pro_v.json`](large_site_schedule_pro_v.json) |
| Why this task | **Agency/portfolio Lovable track**; measure **S21** ultra-compact CSS |
| Speed | S21 **REVERT** (4/5 judge); Site V final timed under **S13** on `:8082` |
| Command | `NANO_PORT=8082 make nano-large-site-pro-v` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S21 attempt (red) | **6.26 s** — menu judge fail; styles CSS OK; archived `out/archive/2026-07-21-fieldwork-s21-failed/` |
| Final make (S13 @8082) | **4.76 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.53 | yes |
| home | 2.85 | yes |
| menu | 2.82 | yes |
| about | 2.83 | yes |
| contact | 2.83 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1601 MB
- Report: [`runs/large_site_schedule_pro_v.json`](runs/large_site_schedule_pro_v.json)

### Notes

- No hand edits to `out/proposal/`
- Ops: if `:8081` busy (docker), use `NANO_PORT=8082`

---

## U — Brightfolio SaaS (`pro-site-U-brightfolio-saas`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-quill-copper-pro-archived/` @ 2026-07-21T16:39:57Z |
| Site | Brightfolio (SaaS portfolio-builder landing + pricing) |
| Schedule | [`large_site_schedule_pro_u.json`](large_site_schedule_pro_u.json) |
| Why this task | Shift from retail boards to **SaaS Lovable-style** landing; measure **S20** compact CSS |
| Speed | S20 **REVERT** (footer truncated); Site U final timed under **S13** |
| Command | `make nano-large-site-pro-u` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S20 attempt (red) | **4.56 s** — `styles_has_footer=false`; archived `out/archive/2026-07-21-brightfolio-s20-failed/` |
| Final make (S13) | **4.83 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.57 | yes |
| home | 2.90 | yes |
| menu | 2.92 | yes |
| about | 2.89 | yes |
| contact | 2.90 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1599 MB
- Report: [`runs/large_site_schedule_pro_u.json`](runs/large_site_schedule_pro_u.json)

### Notes

- No hand edits to `out/proposal/`
- First SaaS-track pro-site in the Lovable expansion table

---

## T — Quill & Copper Stationery (`pro-site-T-quill-copper`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-northwind-kayak-pro-archived/` @ 2026-07-21T16:34:14Z |
| Site | Quill & Copper Stationery (retail / product board) |
| Schedule | [`large_site_schedule_pro_t.json`](large_site_schedule_pro_t.json) |
| Why this task | New stationery domain; measure **S19** (`CTX=9216`) vs N **4.83 s** |
| Speed | S19 **REVERT** (noise); Site T final timed under **S13** |
| Command | `make nano-large-site-pro-t` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S19 attempt (green noise) | **4.81 s** — archived `out/archive/2026-07-21-quill-copper-s19-tie/` |
| Final make (S13) | **4.88 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.61 | yes |
| home | 2.91 | yes |
| menu | 2.94 | yes |
| about | 2.91 | yes |
| contact | 2.92 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1599 MB
- Report: [`runs/large_site_schedule_pro_t.json`](runs/large_site_schedule_pro_t.json)

### Notes

- No hand edits to `out/proposal/`
- Cold-start gain from CTX 9216 was negligible vs styles decode (~3.6 s)

---

## S — Northwind Kayak Outfitters (`pro-site-S-northwind-kayak`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-brickhouse-brew-pro-archived/` @ 2026-07-21T16:25:40Z |
| Site | Northwind Kayak Outfitters (rentals / fee board) |
| Schedule | [`large_site_schedule_pro_s.json`](large_site_schedule_pro_s.json) |
| Why this task | New kayak-rental domain; measure **S18** early-stop vs N **4.83 s** |
| Speed | S18 **REVERT** (0/5); Site S final timed under **S13** |
| Command | `make nano-large-site-pro-s` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S18 attempt (red) | **2.00 s** — echo/stop; archived `out/archive/2026-07-21-northwind-s18-failed/` |
| Final make (S13) | **4.91 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.63 | yes |
| home | 2.94 | yes |
| menu | 2.92 | yes |
| about | 2.96 | yes |
| contact | 2.92 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1599 MB
- Report: [`runs/large_site_schedule_pro_s.json`](runs/large_site_schedule_pro_s.json)

### Notes

- No hand edits to `out/proposal/`
- Do not put stop markers inside copy-exactly prompts for this worker

---

## R — Brickhouse Brewing Co. (`pro-site-R-brickhouse-brew`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-tidepool-surf-pro-archived/` @ 2026-07-21T16:16:49Z |
| Site | Brickhouse Brewing Co. (taproom / tap list) |
| Schedule | [`large_site_schedule_pro_r.json`](large_site_schedule_pro_r.json) |
| Why this task | New brewery domain; measure **S17** (styles750 + health 0.1 + skip_final_stop) vs N **4.83 s** |
| Speed | S17 **REVERT** (CSS form truncated); Site R final timed under **S13** |
| Command | `make nano-large-site-pro-r` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S17 attempt (red) | **4.57 s** — `styles_has_form=false`; archived `out/archive/2026-07-21-brickhouse-s17-failed/` |
| Final make (S13) | **4.90 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.61 | yes |
| home | 2.93 | yes |
| menu | 2.92 | yes |
| about | 2.92 | yes |
| contact | 2.92 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1601 MB
- Report: [`runs/large_site_schedule_pro_r.json`](runs/large_site_schedule_pro_r.json)

### Notes

- No hand edits to `out/proposal/`
- Confirms styles still need **780** tokens under S13 parallel_all (750 truncates form CSS)

---

## Q — Tidepool Surf School (`pro-site-Q-tidepool-surf`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-pinecrest-vet-pro-archived/` @ 2026-07-21T16:09:19Z |
| Site | Tidepool Surf School (lessons / rental fee board) |
| Schedule | [`large_site_schedule_pro_q.json`](large_site_schedule_pro_q.json) |
| Why this task | New surf-school domain; measure **S16** (`-b 4096` / `-ub 1024`) vs N **4.83 s** |
| Speed | S16 **REVERT** (noise); Site Q final timed under **S13** |
| Command | `make nano-large-site-pro-q` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S16 attempt (green noise) | **4.80 s** — archived `out/archive/2026-07-21-tidepool-s16-tie/` |
| Final make (S13) | **4.89 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.61 | yes |
| home | 2.94 | yes |
| menu | 2.94 | yes |
| about | 2.95 | yes |
| contact | 2.91 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1599 MB
- Report: [`runs/large_site_schedule_pro_q.json`](runs/large_site_schedule_pro_q.json)

### Notes

- No hand edits to `out/proposal/`
- S16 batch knobs did not beat styles decode bottleneck

---

## P — Pinecrest Animal Clinic (`pro-site-P-pinecrest-vet`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-marble-rye-pro-archived/` @ 2026-07-21T16:02:10Z |
| Site | Pinecrest Animal Clinic (veterinary services / fee board) |
| Schedule | [`large_site_schedule_pro_p.json`](large_site_schedule_pro_p.json) |
| Why this task | New vet domain; measure **S15** (`-fa on` + `-kvu`) vs N **4.83 s** |
| Speed | S15 **REVERT** (tie); Site P final timed under **S13** |
| Command | `make nano-large-site-pro-p` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S15 attempt (green tie) | **4.83 s** — archived `out/archive/2026-07-21-pinecrest-s15-tie/` |
| Final make (S13) | **4.79 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.52 | yes |
| home | 2.85 | yes |
| menu | 2.82 | yes |
| about | 2.82 | yes |
| contact | 2.81 | yes |

### Quality

- Pass bar: **5/5** · quality_ok · openable **4/4**
- Peak VRAM: ~1601 MB
- Report: [`runs/large_site_schedule_pro_p.json`](runs/large_site_schedule_pro_p.json)

### Notes

- No hand edits to `out/proposal/`
- S15: FA+KVU did not beat styles bottleneck (~3.63 s); keep S13 stack

---

## O — Marble & Rye Deli (`pro-site-O-marble-rye`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-northline-bike-pro-archived/` @ 2026-07-21T15:59:10Z |
| Site | Marble & Rye Deli (food retail / sandwich board) |
| Schedule | [`large_site_schedule_pro_o.json`](large_site_schedule_pro_o.json) |
| Why this task | New deli domain; measure **S14** vs N **4.83 s** |
| Speed | S14 **REVERT**; Site O final timed under **S13** |
| Command | `make nano-large-site-pro-o` |
| Status | **done — GREEN** |

### Timing

| Phase | Wall time |
|-------|-----------|
| S14 attempt (red) | 5.00 s — CSS truncated |
| Final make (S13) | **4.98 s** |
| Orch O0 | skipped |

| Slot (final S13) | elapsed_s | reused |
|------------------|-----------|--------|
| styles | 3.68 | yes |
| home | 3.01 | yes |
| menu | 3.02 | yes |
| about | 2.99 | yes |
| contact | 3.02 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1599 MB** |
| S14 failed archive | `out/archive/2026-07-21-marble-rye-s14-failed/` |
| Report | [`runs/large_site_schedule_pro_o.json`](runs/large_site_schedule_pro_o.json) |

---

## N — Northline Bike Co-op (`pro-site-N-northline-bike`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-bright-harbor-pro-archived/` @ 2026-07-21T15:46:57Z |
| Site | Northline Bike Co-op (shop / tune-up rates) |
| Schedule | [`large_site_schedule_pro_n.json`](large_site_schedule_pro_n.json) |
| Why this task | New co-op retail domain; measure **S13** vs M **5.96 s** |
| Speed | **S13** (all slots parallel + CTX 10240 + `-np 5`) |
| Command | `make nano-large-site-pro-n` |
| Status | **archived** (superseded by O) |
| Archive path | `out/archive/2026-07-21-northline-bike-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **4.83 s** |
| vs Site M S12 baseline | **−19%** |
| Orch O0 | skipped |

| Slot | elapsed_s | reused | note |
|------|-----------|--------|------|
| styles | 3.63 | yes | all-parallel |
| home | 2.96 | yes | all-parallel |
| menu | 2.97 | yes | all-parallel |
| about | 2.96 | yes | all-parallel |
| contact | 2.96 | yes | all-parallel |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1599 MB** |
| Report | [`runs/large_site_schedule_pro_n.json`](runs/large_site_schedule_pro_n.json) |

---

## M — Bright Harbor Marina (`pro-site-M-bright-harbor`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-moss-stone-pro-archived/` @ 2026-07-21T15:43:21Z |
| Site | Bright Harbor Marina (slips / fuel rates) |
| Schedule | [`large_site_schedule_pro_m.json`](large_site_schedule_pro_m.json) |
| Why this task | New marina domain; measure **S12** vs I **9.82 s** |
| Speed | **S12** (parallel HTML + CTX 8192 + `-np 4`) |
| Command | `make nano-large-site-pro-m` |
| Status | **archived** (superseded by N) |
| Archive path | `out/archive/2026-07-21-bright-harbor-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| Full make | **5.96 s** |
| vs Site I S8 best | **−39%** |
| Orch O0 | skipped |

| Slot | elapsed_s | reused | note |
|------|-----------|--------|------|
| styles | 3.32 | no | sequential |
| home | 2.38 | yes | parallel |
| menu | 2.40 | yes | parallel |
| about | 2.40 | yes | parallel |
| contact | 2.38 | yes | parallel |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1577 MB** |
| Report | [`runs/large_site_schedule_pro_m.json`](runs/large_site_schedule_pro_m.json) |

---

## L — Moss & Stone Garden (`pro-site-L-moss-stone`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-willow-whisk-pro-archived/` @ 2026-07-21T15:37:16Z |
| Site | Moss & Stone Garden Center (nursery / prices) |
| Schedule | [`large_site_schedule_pro_l.json`](large_site_schedule_pro_l.json) |
| Why this task | New garden-retail domain; measure **S11** vs I **9.82 s** |
| Speed | S11 **REVERT**; Site L final timed under **S8** |
| Command | `make nano-large-site-pro-l` |
| Status | **archived** (superseded by M) |
| Archive path | `out/archive/2026-07-21-moss-stone-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| S11 attempt (red) | 3.05 s — 0/5 pass |
| Final make (S8) | **10.01 s** |
| Orch O0 | skipped |

| Slot (final S8) | elapsed_s | reused |
|-----------------|-----------|--------|
| styles | 3.43 | no |
| home | 1.59 | yes |
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
| S11 failed archive | `out/archive/2026-07-21-moss-stone-s11-failed/` |
| Report | [`runs/large_site_schedule_pro_l.json`](runs/large_site_schedule_pro_l.json) |

---

## K — Willow & Whisk Bakery (`pro-site-K-willow-whisk`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-copper-lantern-pro-archived/` @ 2026-07-21T15:33:47Z |
| Site | Willow & Whisk Bakery (food retail / menu prices) |
| Schedule | [`large_site_schedule_pro_k.json`](large_site_schedule_pro_k.json) |
| Why this task | New bakery domain; measure **S10** vs I **9.82 s** |
| Speed | S10 **REVERT**; Site K final timed under **S8** |
| Command | `make nano-large-site-pro-k` |
| Status | **archived** (superseded by L) |
| Archive path | `out/archive/2026-07-21-willow-whisk-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| S10 attempt (green but slower) | 10.43 s |
| Final make (S8) | **10.02 s** |
| Orch O0 | skipped |

| Slot (final S8) | elapsed_s | reused |
|-----------------|-----------|--------|
| styles | 3.41 | no |
| home | 1.59 | yes |
| menu | 1.59 | yes |
| about | 1.58 | yes |
| contact | 1.69 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1503 MB** |
| S10 archive | `out/archive/2026-07-21-willow-whisk-s10-slower/` |
| Report | [`runs/large_site_schedule_pro_k.json`](runs/large_site_schedule_pro_k.json) |

---

## J — Copper Lantern Bookstore (`pro-site-J-copper-lantern`)

| Field | Value |
|-------|-------|
| Archive prior | `out/archive/2026-07-21-lumen-photo-pro-archived/` @ 2026-07-21T15:29:50Z |
| Site | Copper Lantern Bookstore (retail / shelves + prices) |
| Schedule | [`large_site_schedule_pro_j.json`](large_site_schedule_pro_j.json) |
| Why this task | New bookstore domain; measure **S9** vs I **9.82 s** |
| Speed | S9 **REVERT**; Site J final timed under **S8** |
| Command | `make nano-large-site-pro-j` |
| Status | **archived** (superseded by K) |
| Archive path | `out/archive/2026-07-21-copper-lantern-pro-archived/` |

### Timing

| Phase | Wall time |
|-------|-----------|
| S9 attempt (red) | 9.60 s — quality fail (`styles_has_form`) |
| Final make (S8) | **10.07 s** |
| Orch O0 | skipped |

| Slot (final S8) | elapsed_s | reused |
|-----------------|-----------|--------|
| styles | 3.43 | no |
| home | 1.60 | yes |
| menu | 1.59 | yes |
| about | 1.60 | yes |
| contact | 1.69 | yes |

### Results

| Check | Value |
|-------|-------|
| Orch | skipped (intentional S5) |
| Workers | **5/5** |
| Pass bar | **MET** |
| Openable | **4/4** |
| Hand edits | **none** |
| Peak VRAM | **1503 MB** |
| S9 failed archive | `out/archive/2026-07-21-copper-lantern-s9-failed/` |
| Report | [`runs/large_site_schedule_pro_j.json`](runs/large_site_schedule_pro_j.json) |

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
| Status | **archived** (superseded by J) |
| Archive path | `out/archive/2026-07-21-lumen-photo-pro-archived/` |

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
