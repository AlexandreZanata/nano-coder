"""Unit tests for publish dataset application service (Stage 7)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nano_coder.application.publish_dataset import publish_synthetic_dataset
from nano_coder.domain.dataset_generation_run import DatasetGenerationState
from nano_coder.domain.dataset_publish import DatasetPublishError
from nano_coder.domain.dataset_publish_config import load_dataset_publish_config
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState

ROOT = Path(__file__).resolve().parents[2]


def _write_draft(draft_dir: Path, *, count: int = 10) -> None:
    draft_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for index in range(1, count + 1):
        record = {
            "id": f"syn-js-{index:04d}",
            "targetLanguage": "JavaScript",
            "instruction": f"Write a JavaScript helper #{index}.",
            "code": f"export function helper{index}() {{ return {index}; }}\n",
            "tags": ["functional", "module", "L2-standard"],
            "metadata": {
                "author": "teacher-model",
                "created": "2026-06-20",
                "source": "synthetic",
            },
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    (draft_dir / "accepted.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (draft_dir / "filter-manifest.json").write_text(
        json.dumps(
            {
                "runId": draft_dir.name,
                "targetLanguage": "JavaScript",
                "state": DatasetGenerationState.COMPLETED.value,
                "syntaxPassRate": 1.0,
                "acceptedCount": count,
                "br005ManualReviewSatisfied": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (draft_dir / "manual-review-manifest.json").write_text(
        json.dumps(
            {
                "runId": draft_dir.name,
                "status": "Approved",
                "br005ManualReviewSatisfied": True,
                "reviewedBy": "operator",
                "reviewedAt": "2026-06-20T12:00:00+00:00",
                "sampleSize": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_publish_synthetic_dataset_writes_immutable_snapshot(tmp_path):
    run_id = "gen-js-smoke"
    draft_dir = tmp_path / "draft" / run_id
    _write_draft(draft_dir)
    config = load_dataset_publish_config(ROOT / "config" / "dataset-publish-v1.yaml")
    events_log = tmp_path / "events.jsonl"

    result = publish_synthetic_dataset(
        draft_id=run_id,
        dataset_version="ds-2026-06-20-js-v1",
        draft_root=tmp_path / "draft",
        published_root=tmp_path / "published",
        config=config,
        published_by="operator",
        events_log=events_log,
        skip_thresholds=True,
    )

    assert result.example_count == 10
    assert (result.published_dir / "examples.jsonl").is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["state"] == SyntheticDatasetState.PUBLISHED.value
    assert (draft_dir / "publish-record.json").is_file()
    assert events_log.read_text(encoding="utf-8").strip().startswith('{"event": "DatasetPublished"')


def test_publish_synthetic_dataset_rejects_existing_version(tmp_path):
    run_id = "gen-js-smoke"
    draft_dir = tmp_path / "draft" / run_id
    _write_draft(draft_dir)
    config = load_dataset_publish_config(ROOT / "config" / "dataset-publish-v1.yaml")
    kwargs = {
        "draft_id": run_id,
        "dataset_version": "ds-2026-06-20-js-v1",
        "draft_root": tmp_path / "draft",
        "published_root": tmp_path / "published",
        "config": config,
        "published_by": "operator",
        "skip_thresholds": True,
    }
    publish_synthetic_dataset(**kwargs)
    with pytest.raises(DatasetPublishError, match="already exists"):
        publish_synthetic_dataset(**kwargs)
