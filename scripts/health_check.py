#!/usr/bin/env python3
"""Environment health check (CPU/GPU)."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", action="store_true", help="Require CUDA GPU")
    args = parser.parse_args()

    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    test_file = logs / ".health_write"
    test_file.write_text("ok", encoding="utf-8")
    test_file.unlink()

    print(f"OK: logs/ writable at {logs}")

    if args.gpu:
        try:
            import torch

            if not torch.cuda.is_available():
                print("ERROR: CUDA not available", file=sys.stderr)
                return 1
            name = torch.cuda.get_device_name(0)
            print(f"OK: GPU {name}")
        except ImportError:
            print("WARN: torch not installed — GPU check skipped")

    if shutil.which("pdflatex"):
        print("OK: pdflatex available")
    else:
        print("WARN: pdflatex not found (paper build local only)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
