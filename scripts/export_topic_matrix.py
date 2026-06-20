#!/usr/bin/env python3
"""Export topic-matrix.csv from config/scope-boundary.yaml."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.scope_boundary import load_scope_boundary  # noqa: E402

OUTPUT = ROOT / ".local" / "review" / "topic-matrix.csv"
SCOPE_PATH = ROOT / "config" / "scope-boundary.yaml"


def main() -> int:
    scope = load_scope_boundary(SCOPE_PATH)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for topic in scope.training_topics:
        rows.append(
            {
                "topic_id": topic.id,
                "language": topic.language.value,
                "difficulty": topic.difficulty,
                "in_seed": "yes",
                "in_synthetic": "yes",
                "in_held_out": "no",
                "pattern": topic.pattern,
            }
        )

    for topic in scope.held_out_topics:
        rows.append(
            {
                "topic_id": topic.id,
                "language": topic.language.value,
                "difficulty": "L3",
                "in_seed": "no",
                "in_synthetic": "no",
                "in_held_out": "yes",
                "pattern": topic.pattern,
            }
        )

    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "topic_id",
                "language",
                "difficulty",
                "in_seed",
                "in_synthetic",
                "in_held_out",
                "pattern",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
