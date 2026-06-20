"""Unit tests for Phase 4 evaluation orchestrator."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from nano_coder.application.phase4_evaluation import run_phase4_evaluation
from nano_coder.domain.phase4_config import load_phase4_config

ROOT = Path(__file__).resolve().parents[2]


def _write_results(root: Path, run_id: str) -> None:
    output_dir = root / run_id
    output_dir.mkdir(parents=True)
    payload = {
        "runId": run_id,
        "compressionMethod": "LoRA",
        "datasetVersion": "ds-2026-06-20-mixed-v1",
        "heldOutTestSetVersion": "held-out-v1",
        "passAt1": 0.8,
        "passAt5": 0.9,
        "syntaxValidityRate": 0.95,
        "trainableParamCount": 1048576,
        "tasks": [{"tags": ["L3-composite"], "passAt1": True, "passAt5": True}],
        "byLanguage": {"JavaScript": {"passAt1": 0.8, "passAt5": 0.9}},
    }
    (output_dir / "results.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_run_phase4_evaluation_analyzes_runs(tmp_path):
    benchmark_root = tmp_path / "benchmarks"
    _write_results(benchmark_root, "bench-lora-smoke-001")

    paths = {
        "held_out": ROOT / "data" / "benchmarks" / "held-out-v1",
        "benchmarks": benchmark_root,
        "checkpoints": tmp_path / "checkpoints",
        "review": tmp_path / "review",
        "phase3_config": ROOT / "config" / "phase3-v1.yaml",
        "smoke_report": tmp_path / "smoke-report.json",
    }

    config = load_phase4_config(ROOT / "config" / "phase4-v1.yaml")
    with patch(
        "nano_coder.application.phase4_evaluation._resolve_paths",
        return_value=paths,
    ):
        result = run_phase4_evaluation(
            config=config,
            project_root=ROOT,
            profile="smoke",
            benchmark_run_ids=["bench-lora-smoke-001"],
        )

    assert result.failed is False
    assert len(result.entries) == 1
    assert (tmp_path / "review" / "phase4-evaluation-report.json").is_file()
