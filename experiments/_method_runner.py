#!/usr/bin/env python3
"""Shared experiment runner for Wave 1 method pipelines."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.method_experiment_pipeline import run_method_experiment  # noqa: E402
from nano_coder.domain.experiment_config import load_phase3_config  # noqa: E402

LOG_PATH = ROOT / "logs" / "experiments.jsonl"
DEFAULT_CONFIG = ROOT / "config" / "phase3-v1.yaml"


def run_experiment(
    experiment_id: str,
    *,
    profile: str = "smoke",
    config_path: Path = DEFAULT_CONFIG,
    run_smoke: bool = False,
) -> int:
    config = load_phase3_config(config_path)
    if experiment_id not in config.experiments:
        print(f"ERROR: unknown experiment {experiment_id}", file=sys.stderr)
        return 1

    spec = config.experiments[experiment_id]
    result = run_method_experiment(
        spec=spec,
        project_root=ROOT,
        profile=profile,
        run_smoke=run_smoke,
    )

    record = {
        "experiment_id": spec.experiment_id,
        "compression_method": spec.compression_method.value,
        "evidence_level": spec.evidence_level,
        "profile": profile,
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

    print(f"OK: {spec.experiment_id} completed (profile={profile})")
    return 0
