#!/usr/bin/env bash
# Download bake-off GGUFs via Hugging Face CLI (Ollama optional).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MODELS="$ROOT/.local/models"

echo "== Nano-Orchestrator model setup (HF → GGUF) =="
mkdir -p "$MODELS"/{qwen3-0.6b,gemma3-270m,smollm2-360m,smollm3-3b,nanbeige4.1-3b}

download() {
  local repo="$1" dir="$2"
  echo "--- hf download $repo → $dir"
  hf download "$repo" --include '*Q4_K_M*' --local-dir "$dir"
}

if command -v ollama >/dev/null 2>&1; then
  echo "Ollama detected — optional pulls:"
  ollama pull qwen2.5-coder:0.5b || true
fi

if ! command -v hf >/dev/null 2>&1; then
  echo "FAIL: hf CLI required (pip install huggingface_hub)" >&2
  exit 1
fi

# Baseline expected pre-seeded; skip if present
if [[ ! -f "$MODELS/qwen25-coder-0.5b/"*.gguf ]]; then
  echo "WARN: baseline qwen25-coder-0.5b GGUF missing — place under .local/models/qwen25-coder-0.5b/"
fi

download "unsloth/Qwen3-0.6B-GGUF" "$MODELS/qwen3-0.6b"
download "bartowski/google_gemma-3-270m-it-GGUF" "$MODELS/gemma3-270m"
download "QuantFactory/SmolLM2-360M-Instruct-GGUF" "$MODELS/smollm2-360m"
download "bartowski/HuggingFaceTB_SmolLM3-3B-GGUF" "$MODELS/smollm3-3b"
download "mradermacher/Nanbeige4.1-3B-GGUF" "$MODELS/nanbeige4.1-3b" \
  || download "tantk/Nanbeige4.1-3B-GGUF" "$MODELS/nanbeige4.1-3b"

echo
echo "DONE. Inventory: nano-orchestrator/benchmarks/models_inventory.md"
echo "NEVER pull MobileLLM-R1 into a product path (FAIR NC)."
find "$MODELS" -name '*.gguf' | sort
