"""Unit tests for report export application (UC-005)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.report_export import export_benchmark_report

ROOT = Path(__file__).resolve().parents[2]


def _write_benchmark_result(root: Path, run_id: str, method: str, pass_at_1: float) -> None:
    output_dir = root / run_id
    output_dir.mkdir(parents=True)
    payload = {
        "runId": run_id,
        "compressionMethod": method,
        "datasetVersion": "ds-2026-06-20-mixed-v1",
        "heldOutTestSetVersion": "held-out-v1",
        "studentModel": "Qwen2.5-Coder-0.5B",
        "passAt1": pass_at_1,
        "passAt5": pass_at_1,
        "peakVramGb": 3.0,
        "durationSeconds": 12.0,
        "trainableParamCount": 1000,
        "byLanguage": {
            "JavaScript": {"passAt1": pass_at_1, "passAt5": pass_at_1},
        },
    }
    (output_dir / "results.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")


def test_export_benchmark_report_writes_markdown_and_json(tmp_path):
    benchmark_root = tmp_path / "benchmarks"
    _write_benchmark_result(benchmark_root, "bench-lora-001", "LoRA", 0.75)
    _write_benchmark_result(benchmark_root, "bench-qlora-001", "QLoRA", 0.80)

    output_path = tmp_path / "reports" / "wave1-ranking.md"
    result = export_benchmark_report(
        run_ids=["bench-lora-001", "bench-qlora-001"],
        benchmark_root=benchmark_root,
        output_path=output_path,
    )

    assert result.record_count == 2
    assert output_path.is_file()
    assert result.summary_path.is_file()
    markdown = output_path.read_text(encoding="utf-8")
    assert "QLoRA" in markdown
    assert "Rank" in markdown
