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
    parser.add_argument("--run-smoke", action="store_true")
    args, _ = parser.parse_known_args(argv)
    return run_experiment(
        "exp_003_dora_baseline",
        profile=args.profile,
        run_smoke=args.run_smoke,
    )


if __name__ == "__main__":
    raise SystemExit(main())
