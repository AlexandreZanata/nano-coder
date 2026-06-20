#!/usr/bin/env python3
"""EXP 001 — LoRA Baseline. Thin orchestrator; training logic goes in src/."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _stub_runner import run_stub


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="ci", choices=["ci", "smoke", "publication"])
    args, _ = parser.parse_known_args(argv)
    return run_stub(
        "exp_001_lora_baseline",
        "LoRA",
        "Established",
        args.profile,
    )


if __name__ == "__main__":
    raise SystemExit(main())
