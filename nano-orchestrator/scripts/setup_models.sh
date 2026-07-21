#!/usr/bin/env bash
# Pull bake-off candidates via Ollama (optional path).
# Primary runtime remains llama.cpp GGUF under .local/models/.
set -euo pipefail

echo "== Nano-Orchestrator model setup =="
echo "Hardware note: unload models between pulls if VRAM is tight."

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama not found — skip pulls. Use HF→GGUF + llama-server instead."
  echo "Baseline already expected at: .local/models/qwen25-coder-0.5b/"
  exit 0
fi

pull() {
  local tag="$1"
  echo "--- ollama pull ${tag}"
  ollama pull "${tag}"
}

pull "qwen2.5-coder:0.5b"
pull "qwen3:0.6b" || echo "WARN: qwen3:0.6b tag may differ — check ollama.com/library"
pull "gemma3:270m" || echo "WARN: gemma3:270m tag may differ"
pull "smollm2:360m" || echo "WARN: smollm2:360m tag may differ"

echo
echo "Orchestrator (~3B) — pull only when ready to benchmark (VRAM):"
echo "  Prefer HF download + GGUF for SmolLM3-3B / Nanbeige4.1-3B"
echo "  See README §6 Phase 1 table"
echo
echo "DONE. Record peak VRAM during bake-off in benchmarks/RESULTS.md"
echo "NEVER pull MobileLLM-R1 into a product path (FAIR NC)."
