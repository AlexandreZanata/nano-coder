#!/usr/bin/env python3
"""Phase 5 — Wave 1 comparative ranking report (UC-005, Part 5)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.phase5_reporting import run_phase5_wave1_report  # noqa: E402
from nano_coder.domain.phase5_config import load_phase5_config  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase5-v1.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export Wave 1 comparative method ranking (Phase 5)",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", choices=["ci", "smoke", "publication"])
    parser.add_argument("--run-ids", nargs="+", help="Benchmark run ids override")
    parser.add_argument(
        "--allow-mixed",
        action="store_true",
        help="Allow ranking with different DatasetVersion values",
    )
    args = parser.parse_args()

    config = load_phase5_config(args.config)
    try:
        result = run_phase5_wave1_report(
            config=config,
            project_root=ROOT,
            profile=args.profile,
            run_ids=args.run_ids,
            allow_mixed=args.allow_mixed,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"OK: Wave {result.wave} ranking exported — "
        f"{result.export.record_count} method(s) → {result.export.output_path}"
    )
    if result.export.footnotes:
        print(f"Footnotes: {len(result.export.footnotes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
