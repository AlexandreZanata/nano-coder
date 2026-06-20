"""Mixed SyntheticDataset publication (Phase 1, Wave 1 MixedLanguages)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.dataset_publish import (
    DatasetPublishError,
    build_dataset_published_event,
    validate_dataset_version,
)
from nano_coder.domain.dataset_publish_config import DatasetPublishConfig
from nano_coder.domain.manual_review import write_jsonl
from nano_coder.domain.published_dataset import load_published_dataset
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class MixedPublishResult:
    dataset_version: str
    example_count: int
    counts_by_language: dict[str, int]
    source_versions: tuple[str, ...]
    published_dir: Path
    manifest_path: Path


def publish_mixed_dataset(
    *,
    source_versions: list[str],
    mixed_version: str,
    published_root: Path,
    publish_config: DatasetPublishConfig,
    published_by: str,
    events_log: Path | None = None,
) -> MixedPublishResult:
    validate_dataset_version(mixed_version, publish_config)

    published_dir = published_root / mixed_version
    if published_dir.exists():
        raise DatasetPublishError(f"published dataset already exists: {published_dir}")

    merged: list[dict[str, Any]] = []
    counts_by_language: dict[str, int] = {}
    for version in source_versions:
        dataset = load_published_dataset(published_root, version)
        merged.extend(dataset.examples)
        lang = dataset.target_language.value
        counts_by_language[lang] = counts_by_language.get(lang, 0) + dataset.example_count

    if len(counts_by_language) < 2:
        raise DatasetPublishError("mixed dataset requires at least two source languages")

    published_dir.mkdir(parents=True, exist_ok=False)
    examples_path = published_dir / publish_config.examples_file
    write_jsonl(examples_path, merged)

    published_at = datetime.now(UTC).isoformat()
    manifest = {
        "datasetVersion": mixed_version,
        "draftId": "+".join(source_versions),
        "state": SyntheticDatasetState.PUBLISHED.value,
        "targetLanguages": sorted(counts_by_language.keys()),
        "exampleCount": len(merged),
        "countsByLanguage": counts_by_language,
        "sourceVersions": source_versions,
        "publishedAt": published_at,
        "publishedBy": published_by,
        "br005Satisfied": all(count >= 1500 for count in counts_by_language.values()),
    }
    manifest_path = published_dir / publish_config.manifest_file
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    index_path = published_root / "published-index.json"
    _append_index(
        index_path,
        {
            "datasetVersion": mixed_version,
            "draftId": manifest["draftId"],
            "targetLanguages": manifest["targetLanguages"],
            "exampleCount": len(merged),
            "state": SyntheticDatasetState.PUBLISHED.value,
            "publishedAt": published_at,
            "publishedBy": published_by,
        },
    )

    if events_log is not None:
        event = build_dataset_published_event(
            dataset_version=mixed_version,
            draft_id=manifest["draftId"],
            target_language=TargetLanguage.JAVASCRIPT,
            example_count=len(merged),
            published_by=published_by,
            published_at=published_at,
        )
        event["targetLanguages"] = manifest["targetLanguages"]
        _append_event(events_log, event)

    return MixedPublishResult(
        dataset_version=mixed_version,
        example_count=len(merged),
        counts_by_language=counts_by_language,
        source_versions=tuple(source_versions),
        published_dir=published_dir,
        manifest_path=manifest_path,
    )


def _append_index(path: Path, entry: dict[str, Any]) -> None:
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
