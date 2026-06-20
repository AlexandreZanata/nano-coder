"""Application service — export comparative benchmark report (UC-005)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.report_comparability import (
    BenchmarkRecord,
    load_benchmark_record,
    rank_benchmark_records,
    validate_comparability,
)


@dataclass(frozen=True)
class ReportExportResult:
    output_path: Path
    summary_path: Path
    record_count: int
    warnings: tuple[str, ...]


def export_benchmark_report(
    *,
    run_ids: list[str],
    benchmark_root: Path,
    output_path: Path,
    tie_breakers: tuple[str, ...] = ("peakVramGb", "durationSeconds", "trainableParamCount"),
    allow_mixed: bool = False,
    events_log: Path | None = None,
) -> ReportExportResult:
    records = [_load_run_record(benchmark_root, run_id) for run_id in run_ids]
    warnings = tuple(validate_comparability(records, allow_mixed=allow_mixed))
    ranked = rank_benchmark_records(records, tie_breakers=tie_breakers)

    payload = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "runIds": run_ids,
        "warnings": list(warnings),
        "ranking": [_record_summary(index + 1, record) for index, record in enumerate(ranked)],
        "records": [record.raw for record in records],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_build_markdown(ranked, warnings), encoding="utf-8")
    summary_path = output_path.with_suffix(".json")
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    _append_event(
        events_log,
        {
            "event": "ExperimentReportGenerated",
            "runIds": run_ids,
            "outputPath": str(output_path),
            "recordCount": len(records),
        },
    )

    return ReportExportResult(
        output_path=output_path,
        summary_path=summary_path,
        record_count=len(records),
        warnings=warnings,
    )


def _load_run_record(benchmark_root: Path, run_id: str) -> BenchmarkRecord:
    path = benchmark_root / run_id / "results.json"
    if not path.is_file():
        raise FileNotFoundError(f"benchmark results not found: {path}")
    return load_benchmark_record(json.loads(path.read_text(encoding="utf-8")))


def _record_summary(rank: int, record: BenchmarkRecord) -> dict[str, Any]:
    return {
        "rank": rank,
        "runId": record.run_id,
        "compressionMethod": record.compression_method,
        "evidenceLevel": record.evidence_level,
        "passAt1": round(record.pass_at_1, 4),
        "passAt5": round(record.pass_at_5, 4),
        "peakVramGb": record.peak_vram_gb,
        "durationSeconds": record.duration_seconds,
        "trainableParamCount": record.trainable_param_count,
    }


def _build_markdown(
    ranked: list[BenchmarkRecord],
    warnings: tuple[str, ...],
) -> str:
    lines = [
        "# Wave 1 Method Ranking",
        "",
        "Comparative benchmark report (UC-005, BR-012).",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend(
        [
            "## Ranking",
            "",
            "| Rank | Method | Evidence | Pass@1 | Pass@5 | VRAM GB | Train s | Params |",
            "|------|--------|----------|--------|--------|---------|---------|--------|",
        ]
    )
    for index, record in enumerate(ranked, start=1):
        vram = "—" if record.peak_vram_gb is None else f"{record.peak_vram_gb:.1f}"
        duration = "—" if record.duration_seconds is None else f"{record.duration_seconds:.1f}"
        params = "—" if record.trainable_param_count is None else str(record.trainable_param_count)
        rank_label = f"r={record.lora_rank}" if record.lora_rank else "—"
        lines.append(
            f"| {index} | {record.compression_method} ({rank_label}) | "
            f"{record.evidence_level} | {record.pass_at_1:.1%} | {record.pass_at_5:.1%} | "
            f"{vram} | {duration} | {params} |"
        )

    lines.extend(["", "## By language", ""])
    for record in ranked:
        lines.append(f"### {record.compression_method} — {record.run_id}")
        lines.append("")
        lines.append("| Language | Pass@1 | Pass@5 |")
        lines.append("|----------|--------|--------|")
        for language, metrics in record.by_language.items():
            lines.append(
                f"| {language} | {metrics.get('passAt1', 0):.1%} | "
                f"{metrics.get('passAt5', 0):.1%} |"
            )
        lines.append("")

    return "\n".join(lines)


def _append_event(path: Path | None, event: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("timestamp", datetime.now(UTC).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
