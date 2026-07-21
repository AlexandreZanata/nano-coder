# Worker / Orchestrator bake-off — MEASURED ONLY

> Measured 2026-07-21 on RTX 4060 8GB via `llama-server` port **8081**.  
> Pass@1 = `JudgeVerdict.passed` after sandbox (no credit for LLM-only opinion).  
> FTL sandbox wired (T-042/T-043); re-measure worker FTL column when re-running bake-off.  
> Orchestrator “Pass@1 JS” column = **JSON-valid MicroTask decompose rate** on 10 sample requests (see `orchestrator_samples.json`).

| Model | Role | Pass@1 JS | Pass@1 HTML | Pass@1 FTL | p50 ms | VRAM MB | tok/s | Notes |
|-------|------|-----------|-------------|------------|--------|---------|-------|-------|
| Qwen2.5-Coder-0.5B | baseline | 0.90 | 0.90 | 0.00 | 357 | 1577 | 367.6 | measured via sandbox Pass@1 |
| Qwen3-0.6B | worker | 0.50 | 0.40 | 0.00 | 438 | 2371 | 311.9 | measured via sandbox Pass@1 |
| Gemma3-270M | worker | 0.50 | 0.30 | 0.00 | 305 | 1367 | 439.5 | measured via sandbox Pass@1 |
| SmolLM2-360M | worker | 0.80 | 0.70 | 0.00 | 299 | 1675 | 443.7 | measured via sandbox Pass@1 |
| SmolLM3-3B | orchestrator | 0.40 |  |  | 7908 | 3547 | 97.8 | JSON-valid MicroTask rate 4/10 |
| Nanbeige4.1-3B | orchestrator | 0.10 |  |  | 1320 | 3761 | 84.6 | JSON-valid MicroTask rate 1/10 |

## Winners (locked in PROGRESS.yaml)

- **Worker A:** `qwen25-coder-0.5b` — best overall Pass@1 (0.60) and strongest JS/HTML on gold v1  
- **Worker B:** `smollm2-360m` — second overall (0.50); faster p50 than baseline  
- **Orchestrator:** `smollm3-3b` — best JSON-valid decompose rate (4/10 vs 1/10); Phase 2 must improve prompting/chat templates  

**Rationale:** Prefer measured gold-set sandbox Pass@1 over published benches. Nanbeige is faster at p50 but much weaker at valid MicroTask JSON under the same one-shot prompt. FTL remains blocked on parser tooling, not model choice.

## Run log

| Date | Command | Host | Notes |
|------|---------|------|-------|
| 2026-07-21 | `start_model_server.sh` + `worker_bakeoff.py --write-results` | RTX 4060 / :8081 | T-020…T-025; JSON runs in `benchmarks/runs/` |
| 2026-07-21 | orchestrator retry with one-shot + `<think>` stop | same | SmolLM3 4/10, Nanbeige 1/10 |

## Phase 3 held_out fine-tune

| Language | Base model | Base Pass@1 | FT model | FT Pass@1 | Gate (≥ base) |
|----------|------------|-------------|----------|-----------|---------------|
| javascript | qwen25-coder-0.5b | 0.50 | qwen25-coder-0.5b-javascript-ft | 0.50 | PASS |
| html | qwen25-coder-0.5b | 1.00 | qwen25-coder-0.5b-html-ft | 1.00 | PASS |
| freemarker | qwen25-coder-0.5b | 1.00 | qwen25-coder-0.5b-freemarker-ft | 1.00 | PASS |
