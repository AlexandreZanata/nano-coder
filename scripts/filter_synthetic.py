#!/usr/bin/env python3
"""Run Stage 5 quality gates on raw synthetic batches (BR-002, BR-005)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.filter_synthetic import filter_synthetic_run  # noqa: E402
from nano_coder.domain.quality_gates_config import load_quality_gates_config  # noqa: E402
from nano_coder.domain.scope_boundary import load_scope_boundary  # noqa: E402
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy  # noqa: E402
from nano_coder.domain.target_language import TargetLanguage  # noqa: E402

DEFAULT_RAW = ROOT / ".local" / "generation" / "raw"
DEFAULT_OUTPUT = ROOT / "data" / "datasets" / "draft"
DEFAULT_REJECTED = ROOT / ".local" / "generation" / "rejected.jsonl"
DEFAULT_SEEDS = ROOT / "data" / "seeds"
DEFAULT_TAXONOMY = ROOT / "config" / "seeds-v1" / "taxonomy.yaml"
DEFAULT_SCOPE = ROOT / "config" / "scope-boundary.yaml"
DEFAULT_GATES = ROOT / "config" / "quality-gates-v1.yaml"
DEFAULT_ESLINT = ROOT / "config" / "eslint" / "eslint.config.js"
DEFAULT_REPORT = ROOT / ".local" / "review" / "filter-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter synthetic batches through quality gates")
    parser.add_argument("--run-id", required=True, help="Run folder under raw generation root")
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--rejected-log", type=Path, default=DEFAULT_REJECTED)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--gates", type=Path, default=DEFAULT_GATES)
    parser.add_argument("--eslint-config", type=Path, default=DEFAULT_ESLINT)
    parser.add_argument("--language", choices=TargetLanguage.values())
    parser.add_argument("--skip-lint", action="store_true")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    raw_dir = args.raw_root / args.run_id
    if not raw_dir.is_dir():
        print(f"ERROR: raw run directory not found: {raw_dir}", file=sys.stderr)
        return 1

    language = TargetLanguage(args.language) if args.language else None
    result = filter_synthetic_run(
        raw_dir=raw_dir,
        output_root=args.output,
        rejected_log=args.rejected_log,
        taxonomy=load_seed_taxonomy(args.taxonomy),
        scope=load_scope_boundary(args.scope),
        config=load_quality_gates_config(args.gates),
        seeds_root=args.seeds,
        eslint_config=args.eslint_config if not args.skip_lint else None,
        skip_lint=args.skip_lint,
        language=language,
    )

    report = {
        "runId": result.run_id,
        "targetLanguage": result.target_language.value,
        "candidateCount": result.candidate_count,
        "acceptedCount": result.accepted_count,
        "rejectedCount": result.rejected_count,
        "syntaxPassRate": round(result.syntax_pass_rate, 4),
        "rejectionsByReason": result.rejections_by_reason,
        "outputDir": str(result.output_dir),
        "br005SyntaxSatisfied": result.br005_syntax_satisfied,
        "br005CountSatisfied": result.br005_count_satisfied,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"OK: {result.accepted_count}/{result.candidate_count} accepted "
        f"(syntax pass rate {result.syntax_pass_rate:.1%}) — {result.output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
