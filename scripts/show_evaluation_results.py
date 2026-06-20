#!/usr/bin/env python3
"""Phase 4 — show evaluation results (operator playbook Part 3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Show Phase 4 evaluation and smoke results")
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / ".local" / "review" / "phase4-evaluation-report.json",
    )
    parser.add_argument(
        "--smoke-report",
        type=Path,
        default=ROOT / ".local" / "review" / "smoke-train-report.json",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=ROOT / ".local" / "review" / "evaluation-results-summary.md",
    )
    args = parser.parse_args()

    if args.summary.is_file():
        print(args.summary.read_text(encoding="utf-8"))

    if args.report.is_file():
        report = json.loads(args.report.read_text(encoding="utf-8"))
        print(f"\nPhase 4 report: {len(report.get('evaluations', []))} evaluation(s)")
    else:
        print(f"Phase 4 report not found: {args.report}", file=sys.stderr)

    if args.smoke_report.is_file():
        smoke = json.loads(args.smoke_report.read_text(encoding="utf-8"))
        print(
            f"Smoke train: Pass@1 {smoke.get('passAt1', 0):.1%} "
            f"gate={'pass' if smoke.get('gateSatisfied') else 'fail'}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
