#!/usr/bin/env python3
"""Stage 8 — smoke LoRA train and held-out evaluation (ADR-002, BR-007)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.smoke_train import run_smoke_train  # noqa: E402
from nano_coder.domain.published_dataset import DatasetNotPublishedError  # noqa: E402
from nano_coder.domain.smoke_train_config import load_smoke_train_config  # noqa: E402
from nano_coder.domain.training_run import TrainingRunState  # noqa: E402

DEFAULT_PUBLISHED = ROOT / "data" / "datasets"
DEFAULT_HELD_OUT = ROOT / "data" / "benchmarks" / "held-out-v1"
DEFAULT_CHECKPOINTS = ROOT / "data" / "checkpoints"
DEFAULT_OUTPUT = ROOT / ".local" / "training" / "smoke"
DEFAULT_CONFIG = ROOT / "config" / "smoke-train-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "smoke-train-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run smoke LoRA train and evaluation")
    parser.add_argument("--dataset-version", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--published", type=Path, default=DEFAULT_PUBLISHED)
    parser.add_argument("--held-out", type=Path, default=DEFAULT_HELD_OUT)
    parser.add_argument("--checkpoints", type=Path, default=DEFAULT_CHECKPOINTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Attempt real GPU training (requires torch/transformers; default is mock dry-run)",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    dry_run = not args.real
    config = load_smoke_train_config(args.config)

    try:
        result = run_smoke_train(
            run_id=args.run_id,
            dataset_version=args.dataset_version,
            published_root=args.published,
            held_out_root=args.held_out,
            checkpoint_root=args.checkpoints,
            output_root=args.output,
            config=config,
            dry_run=dry_run,
        )
    except DatasetNotPublishedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except NotImplementedError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report = {
        "runId": result.run_id,
        "datasetVersion": result.dataset_version,
        "trainingState": result.training_state.value,
        "passAt1": round(result.eval_summary.pass_at_1, 4),
        "gateSatisfied": result.eval_summary.gate_satisfied,
        "iterationRequired": result.iteration_required,
        "manifestPath": str(result.manifest_path),
        "checkpointDir": str(result.checkpoint_dir),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"{'OK' if result.eval_summary.gate_satisfied else 'ITERATE'}: "
        f"Pass@1 {result.eval_summary.pass_at_1:.1%} "
        f"({result.eval_summary.passed_count}/{result.eval_summary.task_count}) "
        f"— {result.manifest_path}"
    )
    return 0 if result.training_state is TrainingRunState.COMPLETED else 1


if __name__ == "__main__":
    raise SystemExit(main())
