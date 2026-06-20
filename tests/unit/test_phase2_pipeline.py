"""Unit tests for Phase 2 LoRA pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from nano_coder.application.phase2_pipeline import run_phase2_lora_pipeline
from nano_coder.domain.phase2_config import load_phase2_config

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


def test_run_phase2_lora_pipeline_smoke_profile(tmp_path):
    published_root = tmp_path / "datasets"
    version = "ds-2026-06-20-mixed-v1"
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
    }

    config = load_phase2_config(ROOT / "config" / "phase2-v1.yaml")
    with patch(
        "nano_coder.application.phase2_pipeline._resolve_paths",
        return_value=paths,
    ):
        result = run_phase2_lora_pipeline(
            config=config,
            project_root=ROOT,
            profile="smoke",
            dataset_version=version,
            train_run_id="train-lora-smoke-test",
            benchmark_run_id="bench-lora-smoke-test",
        )

    assert result.failed is False
    assert len(result.steps) == 2
    assert result.steps[0].step.value == "train"
    assert result.steps[1].step.value == "benchmark"
