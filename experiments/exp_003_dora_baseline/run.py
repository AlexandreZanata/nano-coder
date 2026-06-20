#!/usr/bin/env python3
"""EXP 003 — DoRA Baseline (Phase 3 Wave 1)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _method_runner import run_experiment


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="smoke", choices=["ci", "smoke", "publication"])
    parser.add_argument("--dataset-version")
    parser.add_argument("--run-smoke", action="store_true")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Run real GPU train + benchmark (requires torch/transformers/peft)",
    )
    args, _ = parser.parse_known_args(argv)
    return run_experiment(
        "exp_003_dora_baseline",
        profile=args.profile,
        dataset_version=args.dataset_version,
        run_smoke=args.run_smoke,
        dry_run=not args.real,
    )


if __name__ == "__main__":
    raise SystemExit(main())
