"""Unit tests for training dataset loader."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.domain.target_language import TargetLanguage
from nano_coder.domain.training_dataset import load_training_dataset


def _write_single(root: Path, version: str) -> None:
    published_dir = root / version
    published_dir.mkdir(parents=True)
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "state": "Published",
                "targetLanguage": "JavaScript",
                "datasetVersion": version,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    record = {
        "id": "syn-js-0001",
        "targetLanguage": "JavaScript",
        "instruction": "Write helper.",
        "code": "export function helper() { return 1; }\n",
    }
    (published_dir / "examples.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")


def _write_mixed(root: Path, version: str) -> None:
    published_dir = root / version
    published_dir.mkdir(parents=True)
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "state": "Published",
                "targetLanguages": ["JavaScript", "HTML"],
                "datasetVersion": version,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    lines = [
        json.dumps(
            {
                "id": "syn-js-0001",
                "targetLanguage": "JavaScript",
                "instruction": "js",
                "code": "export function a() {}\n",
            }
        ),
        json.dumps(
            {
                "id": "syn-html-0001",
                "targetLanguage": "HTML",
                "instruction": "html",
                "code": "<!DOCTYPE html><html><body></body></html>\n",
            }
        ),
    ]
    (published_dir / "examples.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_load_training_dataset_single_language(tmp_path):
    version = "ds-2026-06-20-js-v1"
    _write_single(tmp_path, version)
    dataset = load_training_dataset(tmp_path, version)
    assert dataset.is_mixed is False
    assert dataset.target_languages == (TargetLanguage.JAVASCRIPT,)


def test_load_training_dataset_mixed(tmp_path):
    version = "ds-2026-06-20-mixed-v1"
    _write_mixed(tmp_path, version)
    dataset = load_training_dataset(tmp_path, version)
    assert dataset.is_mixed is True
    assert len(dataset.target_languages) == 2
