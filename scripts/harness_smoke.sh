#!/usr/bin/env bash
# nano-coder harness smoke — installed project (agent-rules/, not rules/)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HARNESS="$ROOT/agent-harness"

echo "=== nano-coder harness smoke ==="

test -f "$HARNESS/harness.config.yaml"
test -f "$ROOT/agent-rules/manifest.yaml"
test -f "$ROOT/AGENTS.md"

RULES_PATH="$("$HARNESS/rules-path.sh")"
[[ "$RULES_PATH" == */agent-rules ]] || {
  echo "FAIL: expected agent-rules, got $RULES_PATH" >&2
  exit 1
}

OUT="$("$HARNESS/resolve-rules.sh" api auth)"
echo "$OUT" | grep -q "authorization.md"

python3 - "$ROOT/agent-rules/manifest.yaml" "$ROOT/agent-rules" <<'PY'
import sys
from pathlib import Path
import yaml

manifest = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
rules_dir = Path(sys.argv[2])
for path in manifest.get("always_apply", []):
    assert (rules_dir / path).is_file(), path
for entry in manifest.get("rules", []):
    if entry and entry.get("path"):
        assert (rules_dir / entry["path"]).is_file(), entry["path"]
print("manifest OK")
PY

echo "PASS: nano-coder harness smoke"
