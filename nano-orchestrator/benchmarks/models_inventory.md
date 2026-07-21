# Model inventory — Phase 1 bake-off (T-021)

> Measured on 2026-07-21. Runtime: llama.cpp (`/.local/llama-prism-cuda/llama-server`), port **8081**.  
> Ollama: **not installed** on this host — HF → GGUF path used instead.

## Available locally (ready)

| Model ID | Role | GGUF path | Source repo | License |
|----------|------|-----------|-------------|---------|
| `qwen25-coder-0.5b` | baseline worker | `.local/models/qwen25-coder-0.5b/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf` | Qwen2.5-Coder Instruct Q4_K_M | Apache 2.0 |
| `qwen3-0.6b` | worker | `.local/models/qwen3-0.6b/Qwen3-0.6B-Q4_K_M.gguf` | `unsloth/Qwen3-0.6B-GGUF` | Apache 2.0 |
| `gemma3-270m` | worker | `.local/models/gemma3-270m/google_gemma-3-270m-it-Q4_K_M.gguf` | `bartowski/google_gemma-3-270m-it-GGUF` | Gemma terms |
| `smollm2-360m` | worker | `.local/models/smollm2-360m/SmolLM2-360M-Instruct.Q4_K_M.gguf` | `QuantFactory/SmolLM2-360M-Instruct-GGUF` | Apache 2.0 |
| `smollm3-3b` | orchestrator | `.local/models/smollm3-3b/HuggingFaceTB_SmolLM3-3B-Q4_K_M.gguf` | `bartowski/HuggingFaceTB_SmolLM3-3B-GGUF` | Apache 2.0 |
| `nanbeige4.1-3b` | orchestrator | `.local/models/nanbeige4.1-3b/Nanbeige4.1-3B.Q4_K_M.gguf` | `mradermacher/Nanbeige4.1-3B-GGUF` | Apache 2.0 |

## Explicitly excluded

| Model | Reason |
|-------|--------|
| MobileLLM-R1-* | FAIR NC — research-only, not for Zaflas product |

## HF → GGUF recipe (repeatable)

```bash
cd /path/to/nano-coder
hf download <REPO> --include '*Q4_K_M*' --local-dir .local/models/<model-id>
./nano-orchestrator/scripts/start_model_server.sh <model-id>
```

## Start baseline (T-020)

```bash
./nano-orchestrator/scripts/start_model_server.sh qwen25-coder-0.5b
curl -s http://127.0.0.1:8081/health
curl -s http://127.0.0.1:8081/completion \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"say hi","n_predict":8}'
nvidia-smi --query-gpu=memory.used --format=csv,noheader
```
