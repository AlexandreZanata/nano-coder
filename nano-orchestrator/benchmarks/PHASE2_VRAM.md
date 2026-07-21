# Phase 2 VRAM policy notes (T-036)

Measured 2026-07-21 on RTX 4060 8GB.

| Stage | Peak VRAM MB | Notes |
|-------|--------------|-------|
| Fixed-tasks E2E (workers only) | 1575 | unload between steps via `stop_server` / `start_server` |
| Full E2E (SmolLM3-3B → Qwen0.5B) | 3547 | orchestrator loaded then unloaded before workers |
| Gate | ≤ 6000 | **PASS** (`vram_ok: true`) |

Policy implemented in `application/pipeline.py`:

1. Load orchestrator → decompose  
2. **Stop** server (unload orch)  
3. Load worker model(s) grouped by routing  
4. Stop server after workers  
5. Record peak via `nvidia-smi`
