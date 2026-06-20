#!/usr/bin/env python3
"""Run up to N Wave 1 GPU experiments in parallel (RTX 4060 8 GB budget)."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WAVE1_RUNNERS: dict[str, Path] = {
    "exp_001_lora_baseline": ROOT / "experiments" / "exp_001_lora_baseline" / "run.py",
    "exp_002_qlora_baseline": ROOT / "experiments" / "exp_002_qlora_baseline" / "run.py",
    "exp_003_dora_baseline": ROOT / "experiments" / "exp_003_dora_baseline" / "run.py",
}

DEFAULT_BATCH = [
    "exp_003_dora_baseline",
    "exp_001_lora_baseline",
    "exp_002_qlora_baseline",
]


def _run_one(
    *,
    experiment_id: str,
    profile: str,
    real: bool,
    dataset_version: str | None,
) -> tuple[str, int, str]:
    runner = WAVE1_RUNNERS[experiment_id]
    cmd = [sys.executable, str(runner), "--profile", profile]
    if real:
        cmd.append("--real")
    if dataset_version:
        cmd.extend(["--dataset-version", dataset_version])

    env = os.environ.copy()
    env.setdefault("MLFLOW_DISABLE", "1")
    env.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return experiment_id, completed.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Wave 1 GPU experiments with bounded parallelism",
    )
    parser.add_argument(
        "--experiments",
        nargs="+",
        default=DEFAULT_BATCH,
        choices=sorted(WAVE1_RUNNERS),
        help="Experiment ids (default: DoRA + LoRA smoke + QLoRA smoke)",
    )
    parser.add_argument("--profile", default="smoke", choices=["ci", "smoke", "publication"])
    parser.add_argument("--dataset-version")
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=3,
        help="Max concurrent GPU jobs (default 3 for ~1.5 GB peak each on 8 GB)",
    )
    parser.add_argument(
        "--real",
        action="store_true",
        help="Enable real GPU train + benchmark",
    )
    args = parser.parse_args()

    if args.max_parallel < 1:
        print("ERROR: --max-parallel must be >= 1", file=sys.stderr)
        return 1

    print(
        f"Launching {len(args.experiments)} experiment(s) "
        f"(max_parallel={args.max_parallel}, profile={args.profile}, real={args.real})"
    )

    failures: list[str] = []
    with ProcessPoolExecutor(max_workers=args.max_parallel) as pool:
        futures = {
            pool.submit(
                _run_one,
                experiment_id=experiment_id,
                profile=args.profile,
                real=args.real,
                dataset_version=args.dataset_version,
            ): experiment_id
            for experiment_id in args.experiments
        }
        for future in as_completed(futures):
            experiment_id, code, output = future.result()
            status = "OK" if code == 0 else "FAIL"
            print(f"\n=== {status}: {experiment_id} (exit {code}) ===")
            if output.strip():
                print(output.strip()[-4000:])
            if code != 0:
                failures.append(experiment_id)

    if failures:
        print(f"\nFAILED: {', '.join(failures)}", file=sys.stderr)
        return 1

    print(f"\nOK: {len(args.experiments)} experiment(s) completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
