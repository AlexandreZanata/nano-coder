#!/usr/bin/env python3
"""Sync tracked prompt templates to .local/prompts/ (Stage 4 operator mirror)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "prompts" / "v1"
TARGET = ROOT / ".local" / "prompts"


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    for path in sorted(SOURCE.glob("*.md")):
        shutil.copy2(path, TARGET / path.name)
    readme = TARGET / "README.md"
    readme.write_text(
        "# Teacher prompts — synced from config/prompts/v1/\n\n"
        "Run: `python scripts/export_prompts_to_local.py`\n",
        encoding="utf-8",
    )
    print(f"Synced {len(list(SOURCE.glob('*.md')))} prompts to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
