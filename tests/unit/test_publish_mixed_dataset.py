"""Unit tests for mixed dataset publication."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nano_coder.domain.dataset_publish import DatasetPublishError
from nano_coder.domain.dataset_publish_config import load_dataset_publish_config
from nano_coder.domain.publish_mixed_dataset import publish_mixed_dataset
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState

ROOT = Path(__file__).resolve().parents[2]


def _write_published(root: Path, version: str, language: str, count: int) -> None:
    published_dir = root / version
    published_dir.mkdir(parents=True)
    lines = []
    for index in range(1, count + 1):
        record = {
            "id": f"syn-{language}-{index:04d}",
            "targetLanguage": language,
            "instruction": f"Write example #{index}.",
            "code": f"export function ex{index}() {{ return {index}; }}\n",
            "tags": ["functional", "module", "L2-standard"],
        }
        lines.append(json.dumps(record))
    (published_dir / "examples.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "datasetVersion": version,
                "state": SyntheticDatasetState.PUBLISHED.value,
                "targetLanguage": language,
                "exampleCount": count,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_publish_mixed_dataset_merges_language_versions(tmp_path):
    published_root = tmp_path / "datasets"
    _write_published(published_root, "ds-2026-06-20-js-v1", "JavaScript", 2)
    _write_published(published_root, "ds-2026-06-20-html-v1", "HTML", 2)
    config = load_dataset_publish_config(ROOT / "config" / "dataset-publish-v1.yaml")

    result = publish_mixed_dataset(
        source_versions=["ds-2026-06-20-js-v1", "ds-2026-06-20-html-v1"],
        mixed_version="ds-2026-06-20-mixed-v1",
        published_root=published_root,
        publish_config=config,
        published_by="operator",
    )

    assert result.example_count == 4
    assert result.counts_by_language["JavaScript"] == 2
    assert (result.published_dir / "examples.jsonl").is_file()


def test_publish_mixed_dataset_rejects_single_source(tmp_path):
    published_root = tmp_path / "datasets"
    _write_published(published_root, "ds-2026-06-20-js-v1", "JavaScript", 2)
    config = load_dataset_publish_config(ROOT / "config" / "dataset-publish-v1.yaml")

    with pytest.raises(DatasetPublishError):
        publish_mixed_dataset(
            source_versions=["ds-2026-06-20-js-v1"],
            mixed_version="ds-2026-06-20-mixed-v1",
            published_root=published_root,
            publish_config=config,
            published_by="operator",
        )
