"""Comparability checks and ranking for benchmark reports (UC-005, BR-012)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class IncomparableRunsError(Exception):
    """Benchmark runs cannot be ranked without explicit footnote (BR-012)."""


@dataclass(frozen=True)
class BenchmarkRecord:
    run_id: str
    compression_method: str
    evidence_level: str
    dataset_version: str
    held_out_test_set_version: str
    student_model: str
    pass_at_1: float
    pass_at_5: float
    peak_vram_gb: float | None
    duration_seconds: float | None
    trainable_param_count: int | None
    lora_rank: int | None
    by_language: dict[str, dict[str, float]]
    raw: dict[str, Any]


def load_benchmark_record(payload: dict[str, Any]) -> BenchmarkRecord:
    return BenchmarkRecord(
        run_id=str(payload["runId"]),
        compression_method=str(payload.get("compressionMethod", "Unknown")),
        evidence_level=str(payload.get("evidenceLevel", "Established")),
        dataset_version=str(payload.get("datasetVersion", "")),
        held_out_test_set_version=str(payload.get("heldOutTestSetVersion", "")),
        student_model=str(payload.get("studentModel", "")),
        pass_at_1=float(payload.get("passAt1", 0.0)),
        pass_at_5=float(payload.get("passAt5", 0.0)),
        peak_vram_gb=_optional_float(payload.get("peakVramGb")),
        duration_seconds=_optional_float(payload.get("durationSeconds")),
        trainable_param_count=_optional_int(payload.get("trainableParamCount")),
        lora_rank=_optional_int(payload.get("loraRank")),
        by_language=dict(payload.get("byLanguage", {})),
        raw=payload,
    )


def validate_comparability(
    records: list[BenchmarkRecord],
    *,
    allow_mixed: bool = False,
) -> list[str]:
    if len(records) < 2:
        return []

    warnings: list[str] = []
    datasets = {record.dataset_version for record in records}
    test_sets = {record.held_out_test_set_version for record in records}
    models = {record.student_model for record in records}

    if len(test_sets) > 1:
        raise IncomparableRunsError("held-out test set versions differ across runs")

    if len(models) > 1:
        raise IncomparableRunsError("student models differ across runs")

    if len(datasets) > 1:
        message = f"dataset versions differ: {sorted(datasets)}"
        if allow_mixed:
            warnings.append(message)
        else:
            raise IncomparableRunsError(message)

    return warnings


def rank_benchmark_records(
    records: list[BenchmarkRecord],
    *,
    tie_breakers: tuple[str, ...] = ("peakVramGb", "durationSeconds", "trainableParamCount"),
) -> list[BenchmarkRecord]:
    def sort_key(record: BenchmarkRecord) -> tuple[Any, ...]:
        key: list[Any] = [-record.pass_at_1]
        for field in tie_breakers:
            value = getattr(record, _field_attr(field), None)
            if value is None:
                key.append(float("inf"))
            else:
                key.append(value)
        return tuple(key)

    return sorted(records, key=sort_key)


def _field_attr(field: str) -> str:
    mapping = {
        "peakVramGb": "peak_vram_gb",
        "durationSeconds": "duration_seconds",
        "trainableParamCount": "trainable_param_count",
    }
    return mapping.get(field, field)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
