#!/usr/bin/env bash
# Stop nano-orchestrator llama-server on PORT (default 8081). Keeps :8080 intact.
set -euo pipefail
PORT="${PORT:-8081}"
echo "Stopping :$PORT"
fuser -k "${PORT}/tcp" 2>/dev/null || true
echo "OK"
