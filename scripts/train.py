#!/usr/bin/env python3
"""UC-003 — fine-tune student model (Phase 2 LoRA anchor)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.cli.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(["train", *sys.argv[1:]]))
