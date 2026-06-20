"""Unit tests for benchmark application (UC-004)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.benchmark import run_benchmark
from nano_coder.application.train import run_train
from nano_coder.domain.benchmark_config import load_benchmark_config
from nano_coder.domain.benchmark_run import BenchmarkRunState
from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.train_config import load_train_config

ROOT = Path(__file__).resolve().parents[2]


def _write_mixed_dataset(published_root: Path, version: str) -> None:
    published_dir = published_root / version
    published_dir.mkdir(parents=True)
    record = {
        "id": "syn-js-0001",
        "targetLanguage": "JavaScript",
        "instruction": "Write helper.",
        "code": "export function helper() { return 1; }\n",
    }
    (published_dir / "examples.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "datasetVersion": version,
                "state": "Published",
                "targetLanguages": ["JavaScript"],
                "exampleCount": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_benchmark_dry_run(tmp_path):
    version = "ds-2026-06-20-mixed-v1"
    published_root = tmp_path / "datasets"
    checkpoint_root = tmp_path / "checkpoints"
    _write_mixed_dataset(published_root, version)

    train = run_train(
        run_id="train-lora-smoke-001",
        dataset_version=version,
        compression_method=CompressionMethod.LORA,
        student_model="Qwen2.5-Coder-0.5B",
        data_schedule=DataSchedule.MIXED_LANGUAGES,
        published_root=published_root,
        checkpoint_root=checkpoint_root,
        config=load_train_config(ROOT / "config" / "train-v1.yaml"),
        profile="ci",
        dry_run=True,
    )

    result = run_benchmark(
        run_id="bench-lora-smoke-001",
        checkpoint_dir=train.checkpoint_dir,
        held_out_root=ROOT / "data" / "benchmarks" / "held-out-v1",
        output_root=tmp_path / "benchmarks",
        config=load_benchmark_config(ROOT / "config" / "benchmark-v1.yaml"),
        dry_run=True,
    )

    assert result.benchmark_state is BenchmarkRunState.COMPLETED
    assert result.summary.task_count == 150
    assert result.results_path.is_file()
    assert result.summary_path.is_file()
    payload = json.loads(result.results_path.read_text(encoding="utf-8"))
    assert "JavaScript" in payload["byLanguage"]
