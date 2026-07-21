# Nano-Orchestrator — Task Backlog (100% coverage)

> **Normative execution queue.** Spec = [README.md](README.md). Tracker = [PROGRESS.yaml](PROGRESS.yaml).  
> Mark tasks `[x]` here **and** flip the matching key in `PROGRESS.yaml` after each session.  
> Status legend: `todo` · `doing` · `done` · `blocked` · `skipped`

**Project done when:** all `P0`–`P4` + `GATE` tasks are `done`, and `GATE-001` passes (orchestration ≥ solo 0.5B).  
If `GATE-001` fails → close with negative result (`GATE-NEG`) — still a completed research outcome.

---

## How to use

1. Always work the **lowest ID** that is `todo` and whose deps are `done`.  
2. One task at a time (or a parallel pair only if deps allow and VRAM allows).  
3. DoD must be green before marking done — no “almost”.  
4. Human-authored gold (`T-010`…) — **you** write code/prompts; agents only scaffold tooling.

```bash
cd nano-orchestrator
grep -n '^\- \[ \]' TASKS.md | head -20   # next open tasks
```

---

## Epic map

| Epic | Phase | Goal |
|------|-------|------|
| **E0** | Phase 0 | Contracts + gold data |
| **E1** | Phase 1 | Worker / orchestrator bake-off |
| **E2** | Phase 2 | Minimal orchestrator loop |
| **E3** | Phase 3 | Fine-tune specialized workers |
| **E4** | Phase 4 | Reliable sandboxes + logs |
| **E5** | Phase 5 | Dynamic routing (optional) |
| **EG** | Gates | MVP / project success criteria |
| **EX** | Polish | Docs, ADR promotion, CI hook |

---

## E0 — Contract & gold (Phase 0)

### Already done (scaffold)

- [x] **T-001** Domain entities (`MicroTask`, `WorkerResponse`, `JudgeVerdict`) — `src/.../entities.py`
- [x] **T-002** `Ok`/`Err` Result type — `domain/result.py`
- [x] **T-003** Rubric weights + retry cap — `domain/rubric.py`
- [x] **T-004** Worker cap helper — `domain/task_splitter.py`
- [x] **T-005** Unit tests entities/rubric/cap — `tests/unit/test_entities.py`
- [x] **T-006** `scripts/validate_schema.py`
- [x] **T-007** 3 gold exemplars in `tests/golden/gold_set.json`
- [x] **T-008** Demo `scripts/smoke_runner.py` (stub decompose)

### Open — gold data (human)

- [x] **T-010** Write **js-002…js-010** (9 JS micro-tasks + `gold_code`) → `gold_set.json` + [GOLD_CHECKLIST.md](tests/golden/GOLD_CHECKLIST.md)  
  - **Deps:** T-007 · **DoD:** `validate_schema.py` OK; each `gold_code` passes `node --check`  
  - **Effort:** 0.5–1 day · **Done:** 2026-07-21

- [x] **T-011** Write **html-002…html-010** (9 HTML)  
  - **Deps:** T-007 · **DoD:** schema OK; quality bar in `docs/CODE-QUALITY-STANDARD.md`  
  - **Effort:** 0.5–1 day · **Done:** 2026-07-21

- [x] **T-012** Write **ftl-002…ftl-010** (9 FreeMarker)  
  - **Deps:** T-007 · **DoD:** schema OK; `#list` / `?html` where required by prompt  
  - **Effort:** 0.5–1 day · **Done:** 2026-07-21

- [x] **T-013** Write **held_out.json** ≥6 tasks (2 per language) — never used for fine-tune  
  - **Deps:** T-010, T-011, T-012 · **DoD:** schema validates; IDs `ho-*` listed in GOLD_CHECKLIST  
  - **Effort:** 2–3 h · **Done:** 2026-07-21

- [x] **T-014** Freeze gold v1 — bump `gold_set.json` `"version": 1` note + count ≥30 in PROGRESS  
  - **Deps:** T-010–T-013 · **DoD:** `python scripts/validate_schema.py` + manual count 30+6  
  - **PROGRESS:** `gold_30_handwritten`, `held_out_min_6` · **Done:** 2026-07-21

---

## E1 — Bake-off (Phase 1)

- [x] **T-020** Confirm baseline GGUF path + start llama-server on port `8081`  
  - **Cmd:** `./scripts/start_model_server.sh qwen25-coder-0.5b`  
  - **DoD:** HTTP `/completion` responds; note VRAM MB in RESULTS.md notes  
  - **Effort:** 1 h · **Done:** 2026-07-21 (VRAM ~1577 MB with dual 0.5B; health+completion OK)

- [x] **T-021** Run `./scripts/setup_models.sh` (Ollama path) **or** document HF→GGUF for each candidate  
  - **Deps:** none · **DoD:** checklist of available models in PROGRESS notes  
  - **PROGRESS:** `setup_models` · **Effort:** 2–4 h (downloads) · **Done:** 2026-07-21 — see `benchmarks/models_inventory.md`

- [x] **T-022** Implement `benchmarks/worker_bakeoff.py` for real: load gold → call worker → sandbox → Pass@1 / p50 / VRAM  
  - **Deps:** T-014, T-020 · **DoD:** CLI prints table; writes/appends measured rows  
  - **Effort:** 1 day · **Done:** 2026-07-21

- [x] **T-023** Bake-off **workers:** Qwen2.5-Coder-0.5B (baseline), Qwen3-0.6B, Gemma3-270M, SmolLM2-360M  
  - **Deps:** T-022 · **DoD:** all 4 rows in [RESULTS.md](benchmarks/RESULTS.md) with numbers (not blanks)  
  - **Effort:** 1–2 days · **Done:** 2026-07-21 · MobileLLM-R1 skipped (FAIR NC)

- [x] **T-024** Bake-off **orchestrators:** SmolLM3-3B, Nanbeige4.1-3B (decompose quality on 10 sample requests)  
  - **Deps:** T-022 · **DoD:** RESULTS.md orchestrator rows + qualitative note (JSON valid rate)  
  - **Effort:** 1 day · **Done:** 2026-07-21 (4/10 vs 1/10 after one-shot)

- [x] **T-025** Lock winners in PROGRESS.yaml (`worker_a`, `worker_b`, `orchestrator`)  
  - **Deps:** T-023, T-024 · **DoD:** non-null IDs + one-paragraph rationale in RESULTS.md  
  - **PROGRESS:** `winners_locked`, `results_md_filled` · **Done:** 2026-07-21

---

## E2 — Minimal orchestrator (Phase 2)

- [x] **T-030** Harden `LlamaCppAdapter` (timeouts, stop tokens, token counts) + unit/integration smoke  
  - **Deps:** T-020 · **DoD:** `generate()` returns `Ok` against live server  
  - **PROGRESS:** `llamacpp_adapter` · **Done:** 2026-07-21

- [x] **T-031** Orchestrator prompt + JSON parse → `list[MicroTask]` with schema validation + worker cap  
  - **Deps:** T-030, T-025 · **DoD:** invalid JSON → `Err`; >5 tasks → `Err`  
  - **Done:** 2026-07-21 (`domain/microtask_parser.py`)

- [x] **T-032** Worker dispatch: route by `TargetLanguage` to locked worker model(s)  
  - **Deps:** T-031 · **DoD:** JS/HTML/FTL each get a `WorkerResponse`  
  - **Done:** 2026-07-21 (`worker_dispatch.py` + routing)

- [x] **T-033** Wire `JudgeUseCase` + `CompositeSandbox` into runner (replace demo code)  
  - **Deps:** T-032 · **DoD:** real checks in smoke output  
  - **Done:** 2026-07-21

- [x] **T-034** Retry policy (max 2) + escalate-to-human flag in output package  
  - **Deps:** T-033 · **DoD:** failing task retries ≤2 then `escalate_to_human: true`  
  - **Done:** 2026-07-21

- [x] **T-035** Deterministic merge (ordered by language / task id) → `out/proposal/` print-only  
  - **Deps:** T-034 · **DoD:** no auto-write outside `out/`; README human-gate respected  
  - **Done:** 2026-07-21

- [x] **T-036** VRAM policy: unload orchestrator between decompose and merge (script or keep_alive=0)  
  - **Deps:** T-031 · **DoD:** peak VRAM documented ≤6 GB for full cycle on 2 workers  
  - **PROGRESS:** `keep_alive_vram_policy` · **Done:** 2026-07-21 — peak 3547 MB (see `benchmarks/PHASE2_VRAM.md`)

- [x] **T-037** End-to-end smoke: one multi-language user request → scores JSON  
  - **Deps:** T-035, T-036 · **DoD:** `smoke_runner.py --request "..."` exit 0 with real models  
  - **PROGRESS:** `smoke_e2e` · **Done:** 2026-07-21

---

## E4 — Judge sandboxes (Phase 4) — can overlap late E2

> Prefer completing sandboxes before claiming bake-off Pass@1 is final.

- [x] **T-040** JS sandbox: `node --check` stable + optional `vm` exec when acceptance asks  
  - **Deps:** none · **DoD:** unit tests with good/bad snippets  
  - **PROGRESS:** `js_sandbox` · **Effort:** 0.5 day  
  - **Done:** 2026-07-21 — `exec_ok` → node `vm` with 1s timeout

- [x] **T-041** Install local `html-validate` (project `package.json` or documented npx pin) — no hang  
  - **Deps:** none · **DoD:** `NANO_ORCH_HTML_VALIDATE=1` works &lt;5s after warm  
  - **PROGRESS:** `html_validate` · **Effort:** 0.5 day  
  - **Done:** 2026-07-21 — `package.json` + `.htmlvalidate.json`; warm ~0.15s

- [x] **T-042** FreeMarker JVM spike: `scripts/ftl_parser_spike` builds jar; stdin template → exit 0/1  
  - **Deps:** JDK available · **DoD:** `./build.sh` + README examples pass/fail  
  - **PROGRESS:** `ftl_jvm_spike` · **Effort:** 1 day (risk spike)  
  - **Done:** 2026-07-21

- [x] **T-043** Wire FTL jar into `ftl_sandbox.py`; remove “missing spike” false path for CI local  
  - **Deps:** T-042 · **DoD:** gold FTL `gold_code` all `syntax: true`  
  - **Effort:** 0.5 day  
  - **Done:** 2026-07-21 — gold FTL 10/10 syntax true after `./build.sh`

- [x] **T-044** LLM-as-judge secondary only — never sole pass; document in rubric tests  
  - **Deps:** T-033 · **DoD:** test where sandbox fails + LLM=1.0 still `passed=false`  
  - **PROGRESS:** `llm_secondary_only` · **Effort:** 0.5 day  
  - **Done:** 2026-07-21 — `tests/unit/test_rubric_llm_secondary.py`

- [x] **T-045** Structured LLM call log → `logs/llm_calls.jsonl` (gitignored)  
  - **Deps:** T-030 · **DoD:** each generate appends prompt hash, latency, model id  
  - **Effort:** 0.5 day  
  - **Done:** 2026-07-21 — `llm_call_log.py` wired in `LlamaCppAdapter`

---

## E3 — Specialize workers (Phase 3)

- [ ] **T-050** Export Judge-approved pairs from Phase 1–2 logs → train JSONL (per language)  
  - **Deps:** T-037, T-014 · **DoD:** ≥N examples/language (define N in PROGRESS; suggest ≥50 after teacher distill)  
  - **Effort:** 1 day

- [ ] **T-051** Teacher distillation batch (parent nano-coder pipeline) for micro-tasks if logs thin  
  - **Deps:** T-050 · **DoD:** dataset size meets N; no held_out leakage  
  - **Effort:** 1–3 days (depends on teacher)

- [ ] **T-052** Unsloth QLoRA smoke on winner worker (one language first, e.g. JS)  
  - **Deps:** T-050 · **DoD:** train completes without OOM on 8 GB  
  - **PROGRESS:** `unsloth_smoke` · **Effort:** 1 day

- [ ] **T-053** Export GGUF Q4_K_M + register in `.local/bonsai-chat/models.json` or orchestrator config  
  - **Deps:** T-052 · **DoD:** llama-server loads adapter/merged GGUF  
  - **PROGRESS:** `gguf_export` · **Effort:** 0.5 day

- [ ] **T-054** Score fine-tuned worker on `held_out.json` — Pass@1 ≥ base  
  - **Deps:** T-053, T-013 · **DoD:** RESULTS.md before/after table  
  - **PROGRESS:** `held_out_pass_not_worse`

- [ ] **T-055** Repeat T-052–T-054 for HTML worker  
  - **Deps:** T-054 · **Effort:** 1–2 days

- [ ] **T-056** Repeat T-052–T-054 for FreeMarker worker  
  - **Deps:** T-055 · **Effort:** 1–2 days

---

## E5 — Dynamic orchestration (Phase 5) — only after E2+E4 green

- [ ] **T-060** Unlock Phase 5 in PROGRESS (`phase_5_dynamic.status: pending`)  
  - **Deps:** T-037, T-044, T-045 · **Effort:** 5 min

- [ ] **T-061** Dynamic worker selection from bake-off scores (per language)  
  - **Deps:** T-060, T-025 · **DoD:** config-driven routing table  
  - **Effort:** 1 day

- [ ] **T-062** Adaptive retry budget (0–2) based on task confidence  
  - **Deps:** T-061 · **Effort:** 0.5 day

- [ ] **T-063** Optional debate path for `acceptance` containing `critical` — default OFF  
  - **Deps:** T-061 · **DoD:** flag required; cost note in README  
  - **Effort:** 1 day · **May skip** if GATE already met

---

## EG — Success gates

- [ ] **GATE-001** Orchestration Pass@1 ≥ solo Qwen2.5-Coder-0.5B on full gold set  
  - **Deps:** T-037, T-023, T-040–T-043 · **PROGRESS:** `orchestration_beats_solo_0_5b`

- [ ] **GATE-002** Peak resident VRAM ≤ 6000 MB for full cycle  
  - **Deps:** T-036 · **PROGRESS:** `vram_peak_mb_le_6000`

- [ ] **GATE-003** Latency p50 ≤ Phase-1 target (update target after T-023)  
  - **Deps:** T-023, T-037 · **PROGRESS:** `p50_latency_ms_le_target`

- [ ] **GATE-NEG** If GATE-001 fails: write negative-result note under `experiments/` or `nano-orchestrator/docs/NEGATIVE-RESULT.md` and stop stacking features  
  - **Deps:** GATE-001 failed · **DoD:** documented decision “keep solo 0.5B”

---

## EX — Polish / repo hygiene (100% productization)

- [ ] **T-070** Promote ADR draft → `docs/adr/ADR-00N-multi-nano-orchestration.md` + link in `docs/README.md`  
  - **Deps:** GATE-001 or GATE-NEG · **Effort:** 1 h

- [ ] **T-071** CLI entrypoint `nano-orchestrator` (pyproject scripts) — decompose/judge/bakeoff  
  - **Deps:** T-037 · **Effort:** 0.5 day

- [ ] **T-072** Makefile targets: `make nano-test`, `make nano-smoke`, `make nano-bakeoff`  
  - **Deps:** T-071 · **Effort:** 0.5 day

- [ ] **T-073** CI job (CPU-only): unit tests + `validate_schema.py` (no GPU)  
  - **Deps:** T-005, T-014 · **Effort:** 0.5 day

- [ ] **T-074** Security pass: no auto-persist; log redaction; ASI08 caps asserted in tests  
  - **Deps:** T-034, T-045 · **Effort:** 0.5 day

- [ ] **T-075** Final README pass: mark Status **complete** or **stopped (negative)**; fill all RESULTS blanks  
  - **Deps:** GATE-001 or GATE-NEG · **Effort:** 1 h

---

## Suggested order (critical path)

```text
T-010 → T-011 → T-012 → T-013 → T-014
        ↘ T-040 / T-041 / T-042 (parallel with gold writing)
T-020 → T-021 → T-022 → T-023 → T-024 → T-025
T-030 → T-031 → T-032 → T-033 → T-034 → T-035 → T-036 → T-037
T-043 → T-044 → T-045
GATE-001 / GATE-002 / GATE-003
T-050 → T-052 → T-053 → T-054 → T-055 → T-056
T-060… (optional) → T-070…T-075
```

**Next action right now:** **T-050** (export Judge-approved pairs) — Phase 3 specialize workers.

---

## Session log (append)

| Date | Task IDs | Outcome |
|------|----------|---------|
| 2026-07-21 | T-001…T-008 | Scaffold done; moved to repo |
| 2026-07-21 | T-010…T-014 | Gold v1 frozen (30+6); schema + node checks green |
| 2026-07-21 | T-020…T-025 | Bake-off measured; winners locked (qwen25 / smollm2 / smollm3) |
| 2026-07-21 | T-030…T-037 | Phase 2 pipeline live; E2E smoke peak VRAM 3547 MB |
| 2026-07-21 | T-040…T-045 | Phase 4 sandboxes: JS/HTML/FTL + LLM log + secondary-only |
| | | |
