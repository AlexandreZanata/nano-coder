#!/usr/bin/env python3
"""Stage 6 — submit manual review decisions and finalize run (BR-005)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.manual_review_dataset import (  # noqa: E402
    build_auto_accept_decisions,
    submit_manual_review,
)
from nano_coder.domain.dataset_generation_run import DatasetGenerationState  # noqa: E402
from nano_coder.domain.manual_review import (  # noqa: E402
    ManualReviewError,
    ManualReviewSampleRejected,
    parse_decisions,
)
from nano_coder.domain.manual_review_config import load_manual_review_config  # noqa: E402

DEFAULT_DRAFT = ROOT / "data" / "datasets" / "draft"
DEFAULT_REVIEW = ROOT / ".local" / "review"
DEFAULT_CONFIG = ROOT / "config" / "manual-review-v1.yaml"
DEFAULT_REPORT = ROOT / ".local" / "review" / "submit-review-report.json"


def _load_decisions(args: argparse.Namespace, sample_ids: list[str]) -> dict:
    if args.approve_all:
        return build_auto_accept_decisions(sample_ids)
    if args.decisions is None:
        raise ManualReviewError("provide --decisions or --approve-all")
    raw = json.loads(args.decisions.read_text(encoding="utf-8"))
    return parse_decisions(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Submit manual review decisions for a draft run")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--decisions", type=Path, help="JSON file with reviewed decisions")
    parser.add_argument(
        "--approve-all",
        action="store_true",
        help="Accept every sampled example (smoke / operator shortcut)",
    )
    parser.add_argument("--reviewed-by", default="pipeline-operator")
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--review-root", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    draft_dir = args.draft / args.run_id
    queue_path = args.review_root / args.run_id / "review-queue.json"
    if not queue_path.is_file():
        queue_path = draft_dir / "review-queue.json"
    if not queue_path.is_file():
        print(f"ERROR: review queue not found for run {args.run_id}", file=sys.stderr)
        return 1

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    config = load_manual_review_config(args.config)

    try:
        decisions = _load_decisions(args, queue["sampleExampleIds"])
        result = submit_manual_review(
            run_id=args.run_id,
            draft_dir=draft_dir,
            review_root=args.review_root,
            config=config,
            decisions=decisions,
            reviewed_by=args.reviewed_by,
        )
    except ManualReviewSampleRejected as exc:
        print(f"REJECTED: {exc}", file=sys.stderr)
        return 1
    except ManualReviewError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = {
        "runId": result.run_id,
        "targetLanguage": result.target_language.value,
        "finalState": result.final_state.value,
        "sampleSize": result.outcome.sample_size,
        "acceptedInSample": result.outcome.accepted_count,
        "br005ManualReviewSatisfied": result.outcome.br005_manual_review_satisfied,
        "manifestPath": str(result.manifest_path),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if result.final_state is DatasetGenerationState.COMPLETED:
        print(f"OK: manual review approved — {result.manifest_path}")
        return 0

    print(f"FAILED: manual review rejected — {result.manifest_path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
