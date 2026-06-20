"""Unit tests for published dataset loader (BR-007)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nano_coder.domain.published_dataset import DatasetNotPublishedError, load_published_dataset
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState


def _write_published(root: Path, version: str, *, state: str = "Published") -> None:
    published_dir = root / version
    published_dir.mkdir(parents=True)
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "state": state,
                "targetLanguage": "JavaScript",
                "datasetVersion": version,
                "exampleCount": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    record = {
        "id": "syn-js-0001",
        "targetLanguage": "JavaScript",
        "instruction": "Write a JavaScript helper.",
        "code": "export function helper() { return 1; }\n",
        "tags": ["functional", "module", "L2-standard"],
    }
    (published_dir / "examples.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")


def test_load_published_dataset_reads_examples(tmp_path):
    version = "ds-2026-06-20-js-v1"
    _write_published(tmp_path, version)
    dataset = load_published_dataset(tmp_path, version)
    assert dataset.example_count == 1
    assert dataset.manifest["state"] == SyntheticDatasetState.PUBLISHED.value


def test_load_published_dataset_rejects_draft_state(tmp_path):
    version = "ds-2026-06-20-js-v1"
    _write_published(tmp_path, version, state="Draft")
    with pytest.raises(DatasetNotPublishedError):
        load_published_dataset(tmp_path, version)
