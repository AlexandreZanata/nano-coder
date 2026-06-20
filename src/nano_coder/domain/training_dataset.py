"""Training dataset loader — single-language and mixed (Phase 2, BR-007)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_coder.domain.manual_review import load_jsonl
from nano_coder.domain.published_dataset import DatasetNotPublishedError
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class TrainingDataset:
    dataset_version: str
    is_mixed: bool
    target_languages: tuple[TargetLanguage, ...]
    example_count: int
    examples: tuple[dict[str, Any], ...]
    manifest: dict[str, Any]
    published_dir: Path


def load_training_dataset(published_root: Path, dataset_version: str) -> TrainingDataset:
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

    if "targetLanguages" in manifest:
        languages = tuple(TargetLanguage(lang) for lang in manifest["targetLanguages"])
        return TrainingDataset(
            dataset_version=dataset_version,
            is_mixed=True,
            target_languages=languages,
            example_count=len(examples),
            examples=tuple(examples),
            manifest=manifest,
            published_dir=published_dir,
        )

    language = TargetLanguage(manifest["targetLanguage"])
    return TrainingDataset(
        dataset_version=dataset_version,
        is_mixed=False,
        target_languages=(language,),
        example_count=len(examples),
        examples=tuple(examples),
        manifest=manifest,
        published_dir=published_dir,
    )
