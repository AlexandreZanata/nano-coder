# Worker / Orchestrator bake-off — MEASURED ONLY

> Measured 2026-07-21 on RTX 4060 8GB via `llama-server` port **8081**.  
> Pass@1 = `JudgeVerdict.passed` after sandbox (no credit for LLM-only opinion).  
> Worker FTL column below is the **Phase-1 bake-off** snapshot (FTL sandbox was not wired yet → 0.00).  
> Post-sandbox remasure (GATE run / solo): FTL Pass@1 on gold ≈ **0.90** for `qwen25-coder-0.5b` — see Success gates + `runs/success_gates.json`.  
> Orchestrator columns: Pass@1 JS = **JSON-valid MicroTask decompose rate**; HTML/FTL = **—** (N/A for orch mode).

| Model | Role | Pass@1 JS | Pass@1 HTML | Pass@1 FTL | p50 ms | VRAM MB | tok/s | Notes |
|-------|------|-----------|-------------|------------|--------|---------|-------|-------|
| Qwen2.5-Coder-0.5B | baseline | 0.90 | 0.90 | 0.00* | 357 | 1577 | 367.6 | measured via sandbox Pass@1 |
| Qwen3-0.6B | worker | 0.50 | 0.40 | 0.00* | 438 | 2371 | 311.9 | measured via sandbox Pass@1 |
| Gemma3-270M | worker | 0.50 | 0.30 | 0.00* | 305 | 1367 | 439.5 | measured via sandbox Pass@1 |
| SmolLM2-360M | worker | 0.80 | 0.70 | 0.00* | 299 | 1675 | 443.7 | measured via sandbox Pass@1 |
| SmolLM3-3B | orchestrator | 0.40 | — | — | 7908 | 3547 | 97.8 | JSON-valid MicroTask rate 4/10 |
| Nanbeige4.1-3B | orchestrator | 0.10 | — | — | 1320 | 3761 | 84.6 | JSON-valid MicroTask rate 1/10 |

\*FTL Pass@1 at bake-off time blocked on missing JVM parser (T-042). Not re-run for all workers after spike; use GATE solo FTL 0.90 for qwen25 only.

## Winners (locked in PROGRESS.yaml)

- **Worker A:** `qwen25-coder-0.5b` — best overall Pass@1 (0.60) and strongest JS/HTML on gold v1  
- **Worker B:** `smollm2-360m` — second overall (0.50); faster p50 than baseline  
- **Orchestrator:** `smollm3-3b` — best JSON-valid decompose rate (4/10 vs 1/10); Phase 2 must improve prompting/chat templates  

**Rationale:** Prefer measured gold-set sandbox Pass@1 over published benches. Nanbeige is faster at p50 but much weaker at valid MicroTask JSON under the same one-shot prompt. FTL at bake-off was blocked on parser tooling, not model choice.

## Run log

| Date | Command | Host | Notes |
|------|---------|------|-------|
| 2026-07-21 | `start_model_server.sh` + `worker_bakeoff.py --write-results` | RTX 4060 / :8081 | T-020…T-025; JSON runs in `benchmarks/runs/` |
| 2026-07-21 | orchestrator retry with one-shot + `<think>` stop | same | SmolLM3 4/10, Nanbeige 1/10 |
| 2026-07-21 | `benchmarks/run_success_gates.py` | same | GATE-001 FAIL; see Success gates |

## Phase 3 held_out fine-tune

| Language | Base model | Base Pass@1 | FT model | FT Pass@1 | Gate (≥ base) |
|----------|------------|-------------|----------|-----------|---------------|
| javascript | qwen25-coder-0.5b | 0.50 | qwen25-coder-0.5b-javascript-ft | 0.50 | PASS |
| html | qwen25-coder-0.5b | 1.00 | qwen25-coder-0.5b-html-ft | 1.00 | PASS |
| freemarker | qwen25-coder-0.5b | 1.00 | qwen25-coder-0.5b-freemarker-ft | 1.00 | PASS |

## Success gates (EG)

| Gate | Metric | Threshold | Result |
|------|--------|-----------|--------|
| GATE-001 Pass@1 orch ≥ solo | 0.7333 | ≥ 0.8667 | FAIL |
| GATE-002 peak VRAM ≤ 6000 MB | 1577 | ≤ 6000 | PASS |
| GATE-003 p50 ≤ 2000 ms | 323 | ≤ 2000 | PASS |

- Solo overall Pass@1: **0.8667** (26/30)
- Orch overall Pass@1: **0.7333** (22/30)
- Orch worker p50: **323 ms**; peak VRAM: **1577 MB**
- **Decision:** keep solo `Qwen2.5-Coder-0.5B` — [`docs/NEGATIVE-RESULT.md`](../docs/NEGATIVE-RESULT.md) · ADR-007
