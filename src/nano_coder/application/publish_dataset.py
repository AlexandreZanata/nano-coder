"""Application service — publish draft SyntheticDataset (Stage 7, UC-002)."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.dataset_publish import (
    DatasetPublishError,
    PublishValidationResult,
    build_dataset_published_event,
    build_published_manifest,
    validate_dataset_version,
    validate_publish_preconditions,
    validate_version_language_alignment,
)
from nano_coder.domain.dataset_publish_config import DatasetPublishConfig
from nano_coder.domain.manual_review import load_jsonl
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class PublishResult:
    dataset_version: str
    draft_id: str
    target_language: TargetLanguage
    example_count: int
    published_dir: Path
    manifest_path: Path
    validation: PublishValidationResult


def load_draft_manifests(draft_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    filter_path = draft_dir / "filter-manifest.json"
    review_path = draft_dir / "manual-review-manifest.json"
    if not filter_path.is_file():
        raise DatasetPublishError(f"filter manifest not found: {filter_path}")
    if not review_path.is_file():
        raise DatasetPublishError(f"manual review manifest not found: {review_path}")
    return (
        json.loads(filter_path.read_text(encoding="utf-8")),
        json.loads(review_path.read_text(encoding="utf-8")),
    )


def publish_synthetic_dataset(
    *,
    draft_id: str,
    dataset_version: str,
    draft_root: Path,
    published_root: Path,
    config: DatasetPublishConfig,
    published_by: str,
    events_log: Path | None = None,
    skip_thresholds: bool = False,
) -> PublishResult:
    validate_dataset_version(dataset_version, config)

    draft_dir = draft_root / draft_id
    if not draft_dir.is_dir():
        raise DatasetPublishError(f"draft directory not found: {draft_dir}")

    published_dir = published_root / dataset_version
    if published_dir.exists():
        raise DatasetPublishError(f"published dataset already exists: {published_dir}")

    accepted_path = draft_dir / "accepted.jsonl"
    if not accepted_path.is_file():
        raise DatasetPublishError(f"accepted dataset not found: {accepted_path}")

    accepted_records = load_jsonl(accepted_path)
    if not accepted_records:
        raise DatasetPublishError("cannot publish empty accepted dataset")

    filter_manifest, manual_review_manifest = load_draft_manifests(draft_dir)
    validation = validate_publish_preconditions(
        filter_manifest=filter_manifest,
        manual_review_manifest=manual_review_manifest,
        accepted_count=len(accepted_records),
        config=config,
        skip_thresholds=skip_thresholds,
    )
    if not validation.passed:
        raise DatasetPublishError("; ".join(validation.failures))

    validate_version_language_alignment(dataset_version, validation.target_language, config)

    published_at = datetime.now(UTC).isoformat()
    published_dir.mkdir(parents=True, exist_ok=False)
    examples_path = published_dir / config.examples_file
    shutil.copy2(accepted_path, examples_path)

    br005_satisfied = (
        validation.manual_review_satisfied
        and validation.syntax_pass_rate >= config.min_syntax_pass_rate
        and validation.accepted_count >= config.min_accepted_per_language
    ) or skip_thresholds

    manifest = build_published_manifest(
        dataset_version=dataset_version,
        draft_id=draft_id,
        target_language=validation.target_language,
        example_count=len(accepted_records),
        syntax_pass_rate=validation.syntax_pass_rate,
        published_by=published_by,
        published_at=published_at,
        source_filter_manifest=filter_manifest,
        source_manual_review_manifest=manual_review_manifest,
        br005_satisfied=br005_satisfied,
    )
    manifest_path = published_dir / config.manifest_file
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _append_published_index(
        published_root / "published-index.json",
        {
            "datasetVersion": dataset_version,
            "draftId": draft_id,
            "targetLanguage": validation.target_language.value,
            "exampleCount": len(accepted_records),
            "state": SyntheticDatasetState.PUBLISHED.value,
            "publishedAt": published_at,
            "publishedBy": published_by,
        },
    )

    publish_record = {
        "datasetVersion": dataset_version,
        "publishedAt": published_at,
        "publishedBy": published_by,
        "publishedDir": str(published_dir),
        "state": SyntheticDatasetState.PUBLISHED.value,
    }
    (draft_dir / "publish-record.json").write_text(
        json.dumps(publish_record, indent=2) + "\n",
        encoding="utf-8",
    )

    if events_log is not None:
        event = build_dataset_published_event(
            dataset_version=dataset_version,
            draft_id=draft_id,
            target_language=validation.target_language,
            example_count=len(accepted_records),
            published_by=published_by,
            published_at=published_at,
        )
        _append_event(events_log, event)

    return PublishResult(
        dataset_version=dataset_version,
        draft_id=draft_id,
        target_language=validation.target_language,
        example_count=len(accepted_records),
        published_dir=published_dir,
        manifest_path=manifest_path,
        validation=validation,
    )


def verify_draft_publishable(
    *,
    draft_id: str,
    draft_root: Path,
    config: DatasetPublishConfig,
    skip_thresholds: bool = False,
) -> PublishValidationResult:
    draft_dir = draft_root / draft_id
    filter_manifest, manual_review_manifest = load_draft_manifests(draft_dir)
    accepted_records = load_jsonl(draft_dir / "accepted.jsonl")
    return validate_publish_preconditions(
        filter_manifest=filter_manifest,
        manual_review_manifest=manual_review_manifest,
        accepted_count=len(accepted_records),
        config=config,
        skip_thresholds=skip_thresholds,
    )


def _append_published_index(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []
    if path.is_file():
        index = json.loads(path.read_text(encoding="utf-8"))
    index.append(entry)
    path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def _append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
