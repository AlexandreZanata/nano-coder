#!/usr/bin/env python3
"""Stage 7 — publish draft SyntheticDataset to immutable DatasetVersion (UC-002, BR-005)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.application.publish_dataset import (  # noqa: E402
    publish_synthetic_dataset,
    verify_draft_publishable,
)
from nano_coder.domain.dataset_publish import DatasetPublishError  # noqa: E402
from nano_coder.domain.dataset_publish_config import load_dataset_publish_config  # noqa: E402

DEFAULT_DRAFT = ROOT / "data" / "datasets" / "draft"
DEFAULT_PUBLISHED = ROOT / "data" / "datasets"
DEFAULT_CONFIG = ROOT / "config" / "dataset-publish-v1.yaml"
DEFAULT_EVENTS = ROOT / "data" / "events" / "events.jsonl"
DEFAULT_REPORT = ROOT / ".local" / "review" / "publish-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish a draft synthetic dataset")
    parser.add_argument("--draft-id", required=True, help="Draft run id (folder name)")
    parser.add_argument("--version", help="DatasetVersion id (required unless --verify)")
    parser.add_argument("--published-by", default="pipeline-operator")
    parser.add_argument("--draft", type=Path, default=DEFAULT_DRAFT)
    parser.add_argument("--output", type=Path, default=DEFAULT_PUBLISHED)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--events-log", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument(
        "--skip-thresholds",
        action="store_true",
        help="Skip BR-005 count/syntax thresholds (smoke testing only)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Validate publish preconditions without writing artifacts",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    if not args.verify and not args.version:
        parser.error("--version is required unless --verify is set")

    config = load_dataset_publish_config(args.config)

    try:
        if args.verify:
            validation = verify_draft_publishable(
                draft_id=args.draft_id,
                draft_root=args.draft,
                config=config,
                skip_thresholds=args.skip_thresholds,
            )
            report = {
                "draftId": args.draft_id,
                "passed": validation.passed,
                "acceptedCount": validation.accepted_count,
                "syntaxPassRate": validation.syntax_pass_rate,
                "manualReviewSatisfied": validation.manual_review_satisfied,
                "runState": validation.run_state,
                "failures": list(validation.failures),
            }
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if not validation.passed:
                for failure in validation.failures:
                    print(f"VERIFY FAIL: {failure}", file=sys.stderr)
                return 1
            print(
                f"OK: draft {args.draft_id} is publishable "
                f"({validation.accepted_count} examples)"
            )
            return 0

        result = publish_synthetic_dataset(
            draft_id=args.draft_id,
            dataset_version=args.version,
            draft_root=args.draft,
            published_root=args.output,
            config=config,
            published_by=args.published_by,
            events_log=args.events_log,
            skip_thresholds=args.skip_thresholds,
        )
    except DatasetPublishError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = {
        "datasetVersion": result.dataset_version,
        "draftId": result.draft_id,
        "targetLanguage": result.target_language.value,
        "exampleCount": result.example_count,
        "publishedDir": str(result.published_dir),
        "manifestPath": str(result.manifest_path),
        "br005ManualReviewSatisfied": result.validation.manual_review_satisfied,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"OK: published {result.example_count} examples as {result.dataset_version} "
        f"— {result.published_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
