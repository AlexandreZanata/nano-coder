"""Unit tests for evaluation analysis application."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.evaluation_analyze import analyze_benchmark_results
from nano_coder.domain.phase4_config import load_phase4_config

ROOT = Path(__file__).resolve().parents[2]


def _write_results(root: Path, run_id: str, *, method: str, params: int) -> None:
    output_dir = root / run_id
    output_dir.mkdir(parents=True)
    payload = {
        "runId": run_id,
        "compressionMethod": method,
        "datasetVersion": "ds-2026-06-20-mixed-v1",
        "heldOutTestSetVersion": "held-out-v1",
        "passAt1": 0.75,
        "passAt5": 0.85,
        "syntaxValidityRate": 0.9,
        "trainableParamCount": params,
        "tasks": [
            {"tags": ["L3-composite"], "passAt1": True, "passAt5": True},
            {"tags": ["L3-composite"], "passAt1": False, "passAt5": False},
            {"tags": ["L2-standard"], "passAt1": True, "passAt5": True},
        ],
        "byLanguage": {},
    }
    (output_dir / "results.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_analyze_benchmark_results_writes_evaluation_artifacts(tmp_path):
    benchmark_root = tmp_path / "benchmarks"
    _write_results(benchmark_root, "bench-lora-smoke-001", method="LoRA", params=1000)
    _write_results(benchmark_root, "bench-dora-smoke-001", method="DoRA", params=1200)

    config = load_phase4_config(ROOT / "config" / "phase4-v1.yaml")
    analysis = analyze_benchmark_results(
        run_id="bench-dora-smoke-001",
        benchmark_root=benchmark_root,
        config=config,
        anchor_param_count=1000,
    )

    assert analysis.evaluation_path.is_file()
    assert analysis.summary_path.is_file()
    payload = json.loads(analysis.evaluation_path.read_text(encoding="utf-8"))
    assert payload["paramMatch"]["matched"] is False
    assert len(payload["tagBuckets"]) == 2
