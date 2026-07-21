#!/usr/bin/env python3
"""Worker bake-off runner — fill RESULTS.md with measured numbers only.

Phase 1 stub: loads gold_set, prints task counts, refuses to invent scores.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests" / "golden" / "gold_set.json"
RESULTS = ROOT / "benchmarks" / "RESULTS.md"


def main() -> int:
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    by_lang: dict[str, int] = {}
    for t in tasks:
        by_lang[t["language"]] = by_lang.get(t["language"], 0) + 1
    print(f"Gold tasks: {len(tasks)} → {by_lang}")
    print(
        "Wire LlmBackend + sandbox scoring here (Phase 1 Day 9–11).\n"
        f"Write measured rows into: {RESULTS}"
    )
    if len(tasks) < 30:
        print(
            f"WARN: only {len(tasks)} gold tasks — finish GOLD_CHECKLIST before bake-off.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
