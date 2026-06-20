#!/usr/bin/env python3
"""Phase 3 — Wave 1 method comparison (LoRA, QLoRA, DoRA, FewShot)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.phase3_wave1 import run_phase3_wave1  # noqa: E402
from nano_coder.domain.experiment_config import load_phase3_config  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase3-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "phase3-wave1-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Phase 3 Wave 1 method comparison pipeline",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", default="smoke", choices=["ci", "smoke", "publication"])
    parser.add_argument("--dataset-version", help="DatasetVersion override")
    parser.add_argument(
        "--experiments",
        nargs="+",
        help="Experiment ids (default: all Wave 1 entries in config)",
    )
    parser.add_argument("--run-smoke", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    config = load_phase3_config(args.config)
    result = run_phase3_wave1(
        config=config,
        project_root=ROOT,
        profile=args.profile,
        dataset_version=args.dataset_version,
        experiment_ids=args.experiments,
        run_smoke=args.run_smoke,
    )

    if args.report.is_file():
        print(f"Report: {args.report}")

    for experiment in result.experiments:
        status = "OK" if not experiment.failed else "FAIL"
        print(
            f"{status}: {experiment.experiment_id} "
            f"({experiment.compression_method}) → {experiment.benchmark_run_id}"
        )

    if result.failed:
        print("FAILED: Phase 3 Wave 1 comparison", file=sys.stderr)
        return 1

    print(f"OK: Phase 3 Wave 1 complete — {len(result.experiments)} experiment(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
