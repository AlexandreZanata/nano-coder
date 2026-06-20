"""Unit tests for Phase 5 reporting orchestrator."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from nano_coder.application.phase5_reporting import run_phase5_wave1_report
from nano_coder.domain.phase5_config import load_phase5_config

ROOT = Path(__file__).resolve().parents[2]


def _write_benchmark(root: Path, run_id: str, method: str, pass_at_1: float) -> None:
    output_dir = root / run_id
    output_dir.mkdir(parents=True)
    payload = {
        "runId": run_id,
        "compressionMethod": method,
        "evidenceLevel": "Established",
        "datasetVersion": "ds-2026-06-20-mixed-v1",
        "heldOutTestSetVersion": "held-out-v1",
        "studentModel": "Qwen2.5-Coder-0.5B",
        "passAt1": pass_at_1,
        "passAt5": pass_at_1,
        "peakVramGb": 3.0,
        "durationSeconds": 12.0,
        "trainableParamCount": 1000,
        "loraRank": 16,
        "byLanguage": {
            "JavaScript": {"passAt1": pass_at_1},
            "HTML": {"passAt1": pass_at_1 - 0.05},
            "FreeMarker": {"passAt1": pass_at_1 - 0.1},
        },
    }
    (output_dir / "results.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _config_for_tmp(tmp_path: Path):
    base = load_phase5_config(ROOT / "config" / "phase5-v1.yaml")
    return replace(
        base,
        output_markdown=str(tmp_path / "reports" / "wave1-ranking.md"),
        output_json=str(tmp_path / "reports" / "wave1-ranking.json"),
        phase4_report=".local/review/phase4-evaluation-report.json",
        phase3_report=".local/review/phase3-wave1-report.json",
    )


def test_run_phase5_wave1_report_exports_ranking(tmp_path):
    benchmark_root = tmp_path / "data" / "benchmarks"
    _write_benchmark(benchmark_root, "bench-lora-smoke-001", "LoRA", 0.75)
    _write_benchmark(benchmark_root, "bench-qlora-smoke-001", "QLoRA", 0.80)

    review_dir = tmp_path / ".local" / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "phase4-evaluation-report.json").write_text(
        json.dumps(
            {
                "evaluations": [
                    {"runId": "bench-lora-smoke-001"},
                    {"runId": "bench-qlora-smoke-001"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_phase5_wave1_report(
        config=_config_for_tmp(tmp_path),
        project_root=tmp_path,
        profile="smoke",
    )

    assert result.failed is False
    assert result.export.output_path.is_file()
    markdown = result.export.output_path.read_text(encoding="utf-8")
    assert "JS Pass@1" in markdown
    assert "QLoRA" in markdown


def test_run_phase5_wave1_report_requires_two_runs(tmp_path):
    with pytest.raises(ValueError):
        run_phase5_wave1_report(
            config=_config_for_tmp(tmp_path),
            project_root=tmp_path,
            profile="smoke",
            run_ids=["bench-lora-smoke-001"],
        )
