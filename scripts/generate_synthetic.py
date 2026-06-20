#!/usr/bin/env python3
"""Stage 4 — expand gold seeds via TeacherModel (Self-Instruct / Evol-Instruct)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.expand_dataset import (  # noqa: E402
    load_expansion_config,
    run_expansion,
)
from nano_coder.domain.budget_guard import SeedCountInsufficient  # noqa: E402
from nano_coder.domain.target_language import TargetLanguage  # noqa: E402
from nano_coder.infrastructure.teacher_client import build_teacher_client  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "generation-v1.yaml"
DEFAULT_PROMPTS = ROOT / "config" / "prompts" / "v1"
DEFAULT_SCOPE = ROOT / "config" / "scope-boundary.yaml"
DEFAULT_SEEDS = ROOT / "data" / "seeds"
DEFAULT_REFERENCE = ROOT / "data" / "seeds" / "reference"
DEFAULT_OUTPUT = ROOT / ".local" / "generation" / "raw"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic dataset via TeacherModel")
    parser.add_argument("--language", required=True, choices=list(TargetLanguage.values()))
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--target-count", type=int, default=None)
    parser.add_argument("--max-budget-usd", type=float, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--max-batches", type=int, default=None, help="Limit batches (testing)")
    parser.add_argument("--dry-run", action="store_true", help="Use mock teacher — no API calls")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    config = load_expansion_config(args.config)
    if args.max_budget_usd is not None:
        config.max_budget_usd = args.max_budget_usd
    elif os.environ.get("MAX_BUDGET_USD"):
        config.max_budget_usd = float(os.environ["MAX_BUDGET_USD"])
    if args.batch_size is not None:
        config.batch_size = args.batch_size

    language = TargetLanguage(args.language)
    teacher = build_teacher_client(
        language=language,
        dry_run=args.dry_run,
        model=config.model,
        max_tokens=config.max_tokens,
    )

    try:
        result = run_expansion(
            run_id=args.run_id,
            language=language,
            seeds_root=args.seeds,
            reference_root=args.reference,
            prompt_dir=args.prompts,
            scope_path=args.scope,
            output_root=args.output,
            config=config,
            teacher=teacher,
            target_count=args.target_count,
            max_batches=args.max_batches,
        )
    except SeedCountInsufficient as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if result.failed:
        print(f"FAILED: {result.failure_reason}", file=sys.stderr)
        return 1

    print(
        f"OK: {result.candidate_count} candidates in {result.batch_count} batch(es) "
        f"— ${result.spent_usd:.4f} spent — {result.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
