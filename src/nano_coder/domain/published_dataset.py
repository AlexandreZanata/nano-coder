"""Published SyntheticDataset loader (BR-007)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_coder.domain.manual_review import load_jsonl
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState
from nano_coder.domain.target_language import TargetLanguage


class DatasetNotPublishedError(Exception):
    """Training cannot start — dataset is not in Published state (BR-007)."""


@dataclass(frozen=True)
class PublishedDataset:
    dataset_version: str
    target_language: TargetLanguage
    example_count: int
    examples: tuple[dict[str, Any], ...]
    manifest: dict[str, Any]
    published_dir: Path


def load_published_dataset(published_root: Path, dataset_version: str) -> PublishedDataset:
    published_dir = published_root / dataset_version
    manifest_path = published_dir / "manifest.json"
    examples_path = published_dir / "examples.jsonl"

    if not manifest_path.is_file():
        raise DatasetNotPublishedError(f"published manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    state = manifest.get("state")
    if state != SyntheticDatasetState.PUBLISHED.value:
        raise DatasetNotPublishedError(
            f"dataset {dataset_version} is not Published (state={state})"
        )

    if not examples_path.is_file():
        raise DatasetNotPublishedError(f"published examples not found: {examples_path}")

    examples = load_jsonl(examples_path)
    if not examples:
        raise DatasetNotPublishedError(f"published dataset {dataset_version} is empty")

    return PublishedDataset(
        dataset_version=dataset_version,
        target_language=TargetLanguage(manifest["targetLanguage"]),
        example_count=len(examples),
        examples=tuple(examples),
        manifest=manifest,
        published_dir=published_dir,
    )
