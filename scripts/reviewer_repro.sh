#!/usr/bin/env bash
# Reviewer fast reproduction (~5 min CPU)
set -euo pipefail
cd "$(dirname "$0")/.."
export MLFLOW_DISABLE=1
make docs-check
make hypothesis-check
pytest tests/contracts/ -q
echo "Reviewer repro OK — for full GPU replay see docs/REPRODUCIBILITY.md"
