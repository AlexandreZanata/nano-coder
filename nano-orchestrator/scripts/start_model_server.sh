#!/usr/bin/env bash
# Start (or restart) llama-server on port 8081 for nano-orchestrator bake-off.
# Does NOT touch bonsai-chat on :8080.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOCAL="$ROOT/.local"
BIN="$LOCAL/llama-prism-cuda/llama-server"
PORT="${PORT:-8081}"
MODEL_ID="${1:-qwen25-coder-0.5b}"
CTX="${CTX:-8192}"
NGL="${NGL:-99}"

declare -A MODELS=(
  [qwen25-coder-0.5b]="$LOCAL/models/qwen25-coder-0.5b/qwen2.5-coder-0.5b-instruct-q4_k_m.gguf"
  [qwen3-0.6b]="$LOCAL/models/qwen3-0.6b/Qwen3-0.6B-Q4_K_M.gguf"
  [gemma3-270m]="$LOCAL/models/gemma3-270m/google_gemma-3-270m-it-Q4_K_M.gguf"
  [smollm2-360m]="$LOCAL/models/smollm2-360m/SmolLM2-360M-Instruct.Q4_K_M.gguf"
  [smollm3-3b]="$LOCAL/models/smollm3-3b/HuggingFaceTB_SmolLM3-3B-Q4_K_M.gguf"
  [nanbeige4.1-3b]="$LOCAL/models/nanbeige4.1-3b/Nanbeige4.1-3B.Q4_K_M.gguf"
)

GGUF="${MODELS[$MODEL_ID]:-}"
if [[ -z "$GGUF" || ! -f "$GGUF" ]]; then
  # Fallback: first *.gguf in model dir
  DIR="$LOCAL/models/$MODEL_ID"
  GGUF="$(find "$DIR" -maxdepth 1 -name '*.gguf' | head -1 || true)"
fi
if [[ -z "$GGUF" || ! -f "$GGUF" ]]; then
  echo "FAIL: GGUF not found for $MODEL_ID" >&2
  exit 1
fi
if [[ ! -x "$BIN" ]]; then
  echo "FAIL: llama-server missing at $BIN" >&2
  exit 1
fi

echo "Stopping anything on :$PORT (keeping :8080 intact)..."
fuser -k "${PORT}/tcp" 2>/dev/null || true
sleep 1

LOG="$ROOT/nano-orchestrator/logs/llama-${MODEL_ID}-${PORT}.log"
mkdir -p "$(dirname "$LOG")"

# Match bonsai-chat CUDA library path (pip nvidia-* wheels + local llama libs)
PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CUDA_RUNTIME="$HOME/.pyenv/versions/$(pyenv version-name 2>/dev/null || echo 3.12.2)/lib/python${PY_VER}/site-packages/nvidia/cuda_runtime/lib"
CUBLAS_LIB="$HOME/.pyenv/versions/$(pyenv version-name 2>/dev/null || echo 3.12.2)/lib/python${PY_VER}/site-packages/nvidia/cublas/lib"
# Fallback hard path used by running bonsai server
if [[ ! -d "$CUDA_RUNTIME" ]]; then
  CUDA_RUNTIME="/home/iiii/.pyenv/versions/3.12.2/lib/python3.12/site-packages/nvidia/cuda_runtime/lib"
  CUBLAS_LIB="/home/iiii/.pyenv/versions/3.12.2/lib/python3.12/site-packages/nvidia/cublas/lib"
fi
export LD_LIBRARY_PATH="$LOCAL/llama-prism-cuda:${CUDA_RUNTIME}:${CUBLAS_LIB}:${LD_LIBRARY_PATH:-}"

echo "Starting $MODEL_ID → $GGUF on :$PORT (ngl=$NGL ctx=$CTX)"
nohup "$BIN" \
  -m "$GGUF" \
  --host 127.0.0.1 \
  --port "$PORT" \
  -c "$CTX" \
  -ngl "$NGL" \
  -np 1 \
  >"$LOG" 2>&1 &
echo $! >"$ROOT/nano-orchestrator/logs/llama-${PORT}.pid"

echo -n "Waiting for health"
for _ in $(seq 1 90); do
  if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
    echo " OK"
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader || true
    exit 0
  fi
  echo -n "."
  sleep 1
done
echo
echo "FAIL: server did not become healthy. See $LOG" >&2
exit 1
