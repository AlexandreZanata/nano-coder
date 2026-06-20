"""Unit tests for train application (UC-003)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.train import run_train
from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.train_config import load_train_config
from nano_coder.domain.training_run import TrainingRunState

ROOT = Path(__file__).resolve().parents[2]


def _write_mixed_dataset(published_root: Path, version: str, count: int) -> None:
    published_dir = published_root / version
    published_dir.mkdir(parents=True)
    lines = []
    for index in range(1, count + 1):
        lang = "JavaScript" if index % 2 else "HTML"
        lines.append(
            json.dumps(
                {
                    "id": f"syn-{index:04d}",
                    "targetLanguage": lang,
                    "instruction": f"Write code #{index}.",
                    "code": "export function helper() { return 1; }\n",
                }
            )
        )
    (published_dir / "examples.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "datasetVersion": version,
                "state": "Published",
                "targetLanguages": ["JavaScript", "HTML"],
                "exampleCount": count,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_train_dry_run(tmp_path):
    version = "ds-2026-06-20-mixed-v1"
    published_root = tmp_path / "datasets"
    _write_mixed_dataset(published_root, version, count=20)

    result = run_train(
        run_id="train-lora-smoke-001",
        dataset_version=version,
        compression_method=CompressionMethod.LORA,
        student_model="Qwen2.5-Coder-0.5B",
        data_schedule=DataSchedule.MIXED_LANGUAGES,
        published_root=published_root,
        checkpoint_root=tmp_path / "checkpoints",
        config=load_train_config(ROOT / "config" / "train-v1.yaml"),
        profile="smoke",
        dry_run=True,
    )

    assert result.training_state is TrainingRunState.COMPLETED
    assert result.train_example_count == 20
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["compressionMethod"] == "LoRA"
    assert manifest["dryRun"] is True
