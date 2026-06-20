"""Unit tests for Phase 3 Wave 1 orchestrator."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from nano_coder.application.phase3_wave1 import run_phase3_wave1
from nano_coder.domain.experiment_config import load_phase3_config

ROOT = Path(__file__).resolve().parents[2]


def _write_mixed_dataset(published_root: Path, version: str, count: int) -> None:
    published_dir = published_root / version
    published_dir.mkdir(parents=True)
    lines = []
    for index in range(1, count + 1):
        lines.append(
            json.dumps(
                {
                    "id": f"syn-{index:04d}",
                    "targetLanguage": "JavaScript",
                    "instruction": f"Write helper #{index}.",
                    "code": f"export function helper{index}() {{ return {index}; }}\n",
                }
            )
        )
    (published_dir / "examples.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "datasetVersion": version,
                "state": "Published",
                "targetLanguages": ["JavaScript", "HTML", "FreeMarker"],
                "exampleCount": count,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_phase3_wave1_smoke_profile(tmp_path):
    version = "ds-2026-06-20-mixed-v1"
    published_root = tmp_path / "datasets"
    _write_mixed_dataset(published_root, version, count=10)

    paths = {
        "published": published_root,
        "held_out": ROOT / "data" / "benchmarks" / "held-out-v1",
        "checkpoints": tmp_path / "checkpoints",
        "benchmark_output": tmp_path / "benchmarks",
        "smoke_output": tmp_path / "smoke",
        "train_config": ROOT / "config" / "train-v1.yaml",
        "benchmark_config": ROOT / "config" / "benchmark-v1.yaml",
        "smoke_config": ROOT / "config" / "smoke-train-v1.yaml",
        "events": tmp_path / "events.jsonl",
        "review": tmp_path / "review",
    }

    config = load_phase3_config(ROOT / "config" / "phase3-v1.yaml")
    with patch(
        "nano_coder.application.method_experiment_pipeline.resolve_experiment_paths",
        return_value=paths,
    ):
        result = run_phase3_wave1(
            config=config,
            project_root=ROOT,
            profile="smoke",
            dataset_version=version,
            experiment_ids=["exp_002_qlora_baseline", "fewshot_baseline"],
        )

    assert result.failed is False
    assert len(result.experiments) == 2
    methods = {experiment.compression_method for experiment in result.experiments}
    assert methods == {"QLoRA", "FewShot"}
