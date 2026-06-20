#!/usr/bin/env python3
"""Phase 1 — verify prerequisites before full dataset expansion (Part 1.3)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.phase1_config import (  # noqa: E402
    format_dataset_version,
    load_phase1_config,
)
from nano_coder.domain.phase1_readiness import verify_phase1_readiness  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase1-v1.yaml"
DEFAULT_SEEDS = ROOT / "data" / "seeds"
DEFAULT_PUBLISHED = ROOT / "data" / "datasets"
DEFAULT_REPORT = ROOT / ".local" / "review" / "phase1-readiness-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Phase 1 readiness (seeds + published datasets)",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seeds", type=Path, default=DEFAULT_SEEDS)
    parser.add_argument("--published", type=Path, default=DEFAULT_PUBLISHED)
    parser.add_argument(
        "--check-published",
        action="store_true",
        help="Also verify published versions",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    config = load_phase1_config(args.config)
    versions = None
    if args.check_published:
        versions = {
            language: format_dataset_version(config, language)
            for language in config.required_published_languages
        }

    result = verify_phase1_readiness(
        seeds_root=args.seeds,
        published_root=args.published,
        config=config,
        dataset_versions=versions,
    )

    report = {
        "passed": result.passed,
        "checks": [
            {"name": check.name, "passed": check.passed, "detail": check.detail}
            for check in result.checks
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for check in result.checks:
        status = "OK" if check.passed else "FAIL"
        print(f"{status}: {check.name} — {check.detail}")

    if not result.passed:
        print("FAILED: Phase 1 readiness checks", file=sys.stderr)
        return 1

    print("OK: Phase 1 prerequisites satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
