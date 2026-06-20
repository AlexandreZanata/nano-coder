#!/usr/bin/env python3
"""Phase 1 — publish MixedLanguages dataset from per-language versions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.dataset_publish import DatasetPublishError  # noqa: E402
from nano_coder.domain.dataset_publish_config import load_dataset_publish_config  # noqa: E402
from nano_coder.domain.phase1_config import format_mixed_version, load_phase1_config  # noqa: E402
from nano_coder.domain.publish_mixed_dataset import publish_mixed_dataset  # noqa: E402

DEFAULT_CONFIG = ROOT / "config" / "phase1-v1.yaml"
DEFAULT_PUBLISH = ROOT / "config" / "dataset-publish-v1.yaml"
DEFAULT_PUBLISHED = ROOT / "data" / "datasets"
DEFAULT_EVENTS = ROOT / "data" / "events" / "events.jsonl"
DEFAULT_REPORT = ROOT / ".local" / "review" / "publish-mixed-report.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Publish mixed dataset from language-specific versions",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Source DatasetVersion ids (default: ds-{date}-js/html/fmt-v{wave})",
    )
    parser.add_argument("--version", help="Mixed DatasetVersion id override")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--publish-config", type=Path, default=DEFAULT_PUBLISH)
    parser.add_argument("--published", type=Path, default=DEFAULT_PUBLISHED)
    parser.add_argument("--events-log", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--published-by", default="pipeline-operator")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    phase1 = load_phase1_config(args.config)
    sources = args.sources or [
        phase1.version_template.format(lang=code, wave=phase1.wave, date=phase1.date_stamp)
        for code in ("js", "html", "fmt")
    ]
    mixed_version = args.version or format_mixed_version(phase1)

    try:
        result = publish_mixed_dataset(
            source_versions=sources,
            mixed_version=mixed_version,
            published_root=args.published,
            publish_config=load_dataset_publish_config(args.publish_config),
            published_by=args.published_by,
            events_log=args.events_log,
        )
    except DatasetPublishError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = {
        "datasetVersion": result.dataset_version,
        "exampleCount": result.example_count,
        "countsByLanguage": result.counts_by_language,
        "sourceVersions": list(result.source_versions),
        "manifestPath": str(result.manifest_path),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(
        f"OK: published mixed dataset {result.dataset_version} "
        f"({result.example_count} examples) — {result.published_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
