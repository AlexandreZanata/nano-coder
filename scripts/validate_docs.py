#!/usr/bin/env python3
"""Validate required documentation and research-lab structure (quantun-ia model)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "docs/GLOSSARY.md",
    "docs/ARCHITECTURE.md",
    "docs/BUSINESS-RULES.md",
    "docs/TRAINING-METHODS.md",
    "docs/QUANTUN-IA-PROVEN-METHODS.md",
    "docs/EVALUATION-METHOD.md",
    "docs/RESEARCH-LAB-STRUCTURE.md",
    "docs/HYPOTHESIS-WORKFLOW.md",
    "docs/PAPER-NARRATIVE.md",
    "docs/REPRODUCIBILITY.md",
    "docs/TESTING.md",
    "docs/CI.md",
    "docs/EXPERIMENTS.md",
    "LICENSE",
    "CITATION.cff",
    "CONTRIBUTING.md",
]

REQUIRED_DIRS = [
    "experiments/template",
    "config",
    "paper/sections",
    "tests/unit",
    "tests/contracts",
    ".github/workflows",
]

REQUIRED_PAPER = [
    "paper/main.tex",
    "paper/references.bib",
    "paper/arxiv_metadata.yaml",
    "paper/README.md",
]


def main() -> int:
    errors: list[str] = []

    for rel in REQUIRED_DOCS + REQUIRED_PAPER:
        if not (ROOT / rel).is_file():
            errors.append(f"missing file: {rel}")

    for rel in REQUIRED_DIRS:
        if not (ROOT / rel).is_dir():
            errors.append(f"missing directory: {rel}")

    if not (ROOT / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"):
        errors.append("LICENSE must be MIT")

    exp_dirs = sorted(ROOT.glob("experiments/exp_*"))
    if not exp_dirs:
        errors.append("expected at least one experiments/exp_* directory")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"OK: docs structure validated ({len(REQUIRED_DOCS)} docs, {len(exp_dirs)} experiments)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
