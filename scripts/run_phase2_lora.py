#!/usr/bin/env python3
"""Phase 2 — LoRA anchor pipeline: train + benchmark (operator playbook Part 2)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.phase2_pipeline import (  # noqa: E402
    Phase2Step,
    run_phase2_lora_pipeline,
)
from nano_coder.domain.phase2_config import load_phase2_config  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase2-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "phase2-run-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Phase 2 LoRA anchor pipeline (train + benchmark)",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", default="smoke", choices=["ci", "smoke", "publication"])
    parser.add_argument("--dataset-version", help="Training DatasetVersion override")
    parser.add_argument("--train-run-id")
    parser.add_argument("--benchmark-run-id")
    parser.add_argument("--run-smoke", action="store_true", help="Run Stage 8 smoke gate first")
    parser.add_argument(
        "--stop-after",
        choices=[step.value for step in Phase2Step],
        help="Stop after this step",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    config = load_phase2_config(args.config)
    result = run_phase2_lora_pipeline(
        config=config,
        project_root=ROOT,
        profile=args.profile,
        dataset_version=args.dataset_version,
        train_run_id=args.train_run_id,
        benchmark_run_id=args.benchmark_run_id,
        run_smoke=args.run_smoke,
        stop_after=Phase2Step(args.stop_after) if args.stop_after else None,
    )

    report = {
        "experimentId": result.experiment_id,
        "profile": result.profile,
        "datasetVersion": result.dataset_version,
        "trainRunId": result.train_run_id,
        "benchmarkRunId": result.benchmark_run_id,
        "failed": result.failed,
        "steps": [
            {"step": step.step.value, "success": step.success, "message": step.message}
            for step in result.steps
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for step in result.steps:
        status = "OK" if step.success else "FAIL"
        print(f"{status} [{step.step.value}] {step.message}")

    if result.failed:
        print(f"FAILED: Phase 2 pipeline for {config.experiment_id}", file=sys.stderr)
        return 1

    print(f"OK: Phase 2 complete — {result.train_run_id} → {result.benchmark_run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
