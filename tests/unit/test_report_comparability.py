"""Unit tests for report comparability and ranking (UC-005)."""

from __future__ import annotations

import pytest

from nano_coder.domain.report_comparability import (
    BenchmarkRecord,
    IncomparableRunsError,
    collect_report_footnotes,
    evidence_short_label,
    load_benchmark_record,
    rank_benchmark_records,
    validate_comparability,
)


def _record(
    run_id: str,
    method: str,
    pass_at_1: float,
    *,
    vram: float = 3.0,
    duration: float = 10.0,
    params: int = 1000,
) -> BenchmarkRecord:
    return load_benchmark_record(
        {
            "runId": run_id,
            "compressionMethod": method,
            "datasetVersion": "ds-2026-06-20-mixed-v1",
            "heldOutTestSetVersion": "held-out-v1",
            "studentModel": "Qwen2.5-Coder-0.5B",
            "passAt1": pass_at_1,
            "passAt5": pass_at_1,
            "peakVramGb": vram,
            "durationSeconds": duration,
            "trainableParamCount": params,
            "byLanguage": {},
        }
    )


def test_rank_benchmark_records_orders_by_pass_at_1():
    ranked = rank_benchmark_records(
        [
            _record("bench-a", "LoRA", 0.7),
            _record("bench-b", "QLoRA", 0.8),
        ]
    )
    assert ranked[0].run_id == "bench-b"


def test_validate_comparability_rejects_mixed_datasets():
    records = [
        _record("bench-a", "LoRA", 0.7),
        load_benchmark_record(
            {
                "runId": "bench-b",
                "compressionMethod": "QLoRA",
                "datasetVersion": "ds-other",
                "heldOutTestSetVersion": "held-out-v1",
                "studentModel": "Qwen2.5-Coder-0.5B",
                "passAt1": 0.8,
                "passAt5": 0.8,
                "byLanguage": {},
            }
        ),
    ]
    with pytest.raises(IncomparableRunsError):
        validate_comparability(records)


def test_collect_report_footnotes_flags_speculative():
    record = load_benchmark_record(
        {
            "runId": "bench-spec-001",
            "compressionMethod": "DecoherenceRegularization",
            "evidenceLevel": "Speculative",
            "passAt1": 0.5,
            "passAt5": 0.5,
            "byLanguage": {},
        }
    )
    footnotes = collect_report_footnotes([record])
    assert len(footnotes) == 1
    assert evidence_short_label("Speculative") == "L4"
