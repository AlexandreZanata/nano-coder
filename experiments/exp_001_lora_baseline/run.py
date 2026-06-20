#!/usr/bin/env python3
"""EXP 001 — LoRA Baseline (Phase 2 anchor)."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.phase2_pipeline import run_phase2_lora_pipeline  # noqa: E402
from nano_coder.domain.phase2_config import load_phase2_config  # noqa: E402

LOG_PATH = ROOT / "logs" / "experiments.jsonl"
DEFAULT_CONFIG = ROOT / "config" / "phase2-v1.yaml"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="smoke", choices=["ci", "smoke", "publication"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-smoke", action="store_true")
    args, _ = parser.parse_known_args(argv)

    config = load_phase2_config(args.config)
    result = run_phase2_lora_pipeline(
        config=config,
        project_root=ROOT,
        profile=args.profile,
        run_smoke=args.run_smoke,
    )

    record = {
        "experiment_id": config.experiment_id,
        "compression_method": config.compression_method.value,
        "evidence_level": config.evidence_level,
        "profile": args.profile,
        "status": "completed" if not result.failed else "failed",
        "dataset_version": result.dataset_version,
        "train_run_id": result.train_run_id,
        "benchmark_run_id": result.benchmark_run_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    for step in result.steps:
        status = "OK" if step.success else "FAIL"
        print(f"{status} [{step.step.value}] {step.message}")

    if result.failed:
        return 1

    print(f"OK: {config.experiment_id} completed (profile={args.profile})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
