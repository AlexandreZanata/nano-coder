#!/usr/bin/env python3
"""Stage 6 — prepare manual review sample (≥5%) for PipelineOperator (BR-005)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.manual_review_dataset import prepare_manual_review  # noqa: E402
from nano_coder.domain.manual_review import ManualReviewError  # noqa: E402
from nano_coder.domain.manual_review_config import load_manual_review_config  # noqa: E402

DEFAULT_DRAFT = ROOT / "data" / "datasets" / "draft"
DEFAULT_REVIEW = ROOT / ".local" / "review"
DEFAULT_CONFIG = ROOT / "config" / "manual-review-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "prepare-review-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare manual review sample for a draft run")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--review-root", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    draft_dir = args.draft / args.run_id
    if not draft_dir.is_dir():
        print(f"ERROR: draft directory not found: {draft_dir}", file=sys.stderr)
        return 1

    try:
        config = load_manual_review_config(args.config)
        result = prepare_manual_review(
            run_id=args.run_id,
            draft_dir=draft_dir,
            review_root=args.review_root,
            config=config,
        )
    except ManualReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = {
        "runId": result.run_id,
        "targetLanguage": result.target_language.value,
        "acceptedCount": result.accepted_count,
        "sampleSize": result.sample_size,
        "sampleRate": config.sample_rate,
        "samplePath": str(result.sample_path),
        "queuePath": str(result.queue_path),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"OK: sample {result.sample_size}/{result.accepted_count} "
        f"({result.sample_size / result.accepted_count:.1%}) — {result.sample_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
