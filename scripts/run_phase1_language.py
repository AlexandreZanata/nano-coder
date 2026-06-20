#!/usr/bin/env python3
"""Phase 1 — run Stages 4–8 pipeline for one TargetLanguage (operator playbook Part 1.2)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.phase1_pipeline import (  # noqa: E402
    Phase1Step,
    run_phase1_language_pipeline,
)
from nano_coder.domain.phase1_config import load_phase1_config  # noqa: E402
from nano_coder.domain.target_language import TargetLanguage  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase1-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "phase1-run-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Phase 1 synthetic data pipeline for one language",
    )
    parser.add_argument("--language", required=True, choices=list(TargetLanguage.values()))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-id")
    parser.add_argument("--version", help="DatasetVersion override")
    parser.add_argument("--target-count", type=int)
    parser.add_argument("--max-batches", type=int, help="Limit generation batches (smoke testing)")
    parser.add_argument(
        "--real-generation",
        action="store_true",
        help="Use teacher API instead of mock",
    )
    parser.add_argument("--skip-lint", action="store_true")
    parser.add_argument(
        "--skip-thresholds",
        action="store_true",
        help="Skip BR-005 publish count gate",
    )
    parser.add_argument(
        "--approve-all",
        action="store_true",
        help="Auto-approve manual review sample",
    )
    parser.add_argument("--no-smoke-train", action="store_true")
    parser.add_argument(
        "--stop-after",
        choices=[step.value for step in Phase1Step],
        help="Stop after this step (for staged operator runs)",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    base = load_phase1_config(args.config)
    language = TargetLanguage(args.language)
    config = _apply_overrides(base, args)

    result = run_phase1_language_pipeline(
        language=language,
        config=config,
        project_root=ROOT,
        run_id=args.run_id,
        dataset_version=args.version,
        target_count=args.target_count,
        max_batches=args.max_batches,
        stop_after=Phase1Step(args.stop_after) if args.stop_after else None,
    )

    report = {
        "language": result.language.value,
        "runId": result.run_id,
        "datasetVersion": result.dataset_version,
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
        print(f"FAILED: Phase 1 pipeline for {language.value}", file=sys.stderr)
        return 1

    print(f"OK: Phase 1 complete — {result.dataset_version}")
    return 0


def _apply_overrides(base, args: argparse.Namespace):
    from dataclasses import replace

    updates = {}
    if args.real_generation:
        updates["dry_run_generation"] = False
    if args.skip_lint:
        updates["skip_lint"] = True
    if args.skip_thresholds:
        updates["skip_publish_thresholds"] = True
    if args.approve_all:
        updates["auto_approve_review"] = True
    if args.no_smoke_train:
        updates["run_smoke_train"] = False
    if args.target_count is not None:
        updates["target_count"] = args.target_count
    return replace(base, **updates) if updates else base


if __name__ == "__main__":
    raise SystemExit(main())
