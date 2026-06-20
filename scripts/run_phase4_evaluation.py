#!/usr/bin/env python3
"""Phase 4 — full held-out evaluation analysis (EVALUATION-METHOD.md, Part 3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.phase4_evaluation import run_phase4_evaluation  # noqa: E402
from nano_coder.domain.phase4_config import load_phase4_config  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase4-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "phase4-evaluation-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Phase 4 evaluation analysis on Wave 1 benchmark results",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", choices=["ci", "smoke", "publication"])
    parser.add_argument("--run-ids", nargs="+", help="Benchmark run ids override")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    config = load_phase4_config(args.config)
    result = run_phase4_evaluation(
        config=config,
        project_root=ROOT,
        profile=args.profile,
        benchmark_run_ids=args.run_ids,
    )

    if args.report.is_file():
        report = json.loads(args.report.read_text(encoding="utf-8"))
        for check in report.get("readinessChecks", []):
            status = "OK" if check["passed"] else "FAIL"
            print(f"{status}: {check['name']} — {check['detail']}")
        for entry in report.get("evaluations", []):
            print(
                f"OK: {entry['compressionMethod']} Pass@1 {entry['passAt1']:.1%} "
                f"→ {entry['evaluationPath']}"
            )

    if result.failed:
        print("FAILED: Phase 4 evaluation", file=sys.stderr)
        return 1

    print(f"OK: Phase 4 evaluation complete — {len(result.entries)} run(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
