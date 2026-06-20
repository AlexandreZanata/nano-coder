"""Comparability checks and ranking for benchmark reports (UC-005, BR-012)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class IncomparableRunsError(Exception):
    """Benchmark runs cannot be ranked without explicit footnote (BR-012)."""


_EVIDENCE_LABELS = {
    "Established": "L1",
    "NovelApplication": "L3",
    "QuantumInspired": "L2",
    "Speculative": "L4",
}


@dataclass(frozen=True)
class ReportFootnote:
    run_id: str
    compression_method: str
    reason: str


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
    param_match_footnote_required: bool
    tag_buckets: tuple[dict[str, Any], ...]
    raw: dict[str, Any]


def evidence_short_label(evidence_level: str) -> str:
    return _EVIDENCE_LABELS.get(evidence_level, evidence_level)


def rank_parameter_label(record: BenchmarkRecord) -> str:
    if record.lora_rank is not None:
        return f"r={record.lora_rank}"
    return "—"


def load_benchmark_record(payload: dict[str, Any]) -> BenchmarkRecord:
    param_match = payload.get("paramMatch") or {}
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
        param_match_footnote_required=bool(param_match.get("footnoteRequired", False)),
        tag_buckets=tuple(payload.get("tagBuckets", [])),
        raw=payload,
    )


def load_benchmark_record_from_dir(benchmark_root: Path, run_id: str) -> BenchmarkRecord:
    for name in ("evaluation.json", "results.json"):
        path = benchmark_root / run_id / name
        if path.is_file():
            return load_benchmark_record(json.loads(path.read_text(encoding="utf-8")))
    raise FileNotFoundError(f"benchmark artifacts not found for run: {run_id}")


def collect_report_footnotes(records: list[BenchmarkRecord]) -> tuple[ReportFootnote, ...]:
    footnotes: list[ReportFootnote] = []
    for record in records:
        if record.param_match_footnote_required:
            footnotes.append(
                ReportFootnote(
                    run_id=record.run_id,
                    compression_method=record.compression_method,
                    reason="BR-014 trainable params differ from anchor by > tolerance",
                )
            )
        if record.evidence_level == "Speculative":
            footnotes.append(
                ReportFootnote(
                    run_id=record.run_id,
                    compression_method=record.compression_method,
                    reason="L4 Speculative — not ranked as best without explicit label",
                )
            )
    return tuple(footnotes)


def pass_at_1_for_language(record: BenchmarkRecord, language: str) -> float | None:
    metrics = record.by_language.get(language)
    if metrics is None:
        return None
    return float(metrics.get("passAt1", 0.0))


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
