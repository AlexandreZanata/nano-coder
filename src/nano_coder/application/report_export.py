"""Application service — Wave 1 comparative report export (UC-005, Phase 5)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.report_comparability import (
    BenchmarkRecord,
    ReportFootnote,
    collect_report_footnotes,
    evidence_short_label,
    load_benchmark_record_from_dir,
    pass_at_1_for_language,
    rank_benchmark_records,
    rank_parameter_label,
    validate_comparability,
)


@dataclass(frozen=True)
class ReportExportResult:
    output_path: Path
    summary_path: Path
    record_count: int
    warnings: tuple[str, ...]
    footnotes: tuple[ReportFootnote, ...]


def export_benchmark_report(
    *,
    run_ids: list[str],
    benchmark_root: Path,
    output_path: Path,
    languages: tuple[str, ...] = ("JavaScript", "HTML", "FreeMarker"),
    tie_breakers: tuple[str, ...] = ("peakVramGb", "durationSeconds", "trainableParamCount"),
    allow_mixed: bool = False,
    events_log: Path | None = None,
) -> ReportExportResult:
    records = [load_benchmark_record_from_dir(benchmark_root, run_id) for run_id in run_ids]
    warnings = tuple(validate_comparability(records, allow_mixed=allow_mixed))
    footnotes = collect_report_footnotes(records)
    ranked = rank_benchmark_records(records, tie_breakers=tie_breakers)

    payload = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "runIds": run_ids,
        "warnings": list(warnings),
        "footnotes": [
            {
                "runId": footnote.run_id,
                "compressionMethod": footnote.compression_method,
                "reason": footnote.reason,
            }
            for footnote in footnotes
        ],
        "ranking": [
            _record_summary(index + 1, record, languages)
            for index, record in enumerate(ranked)
        ],
        "records": [record.raw for record in records],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _build_markdown(ranked, warnings, footnotes, languages),
        encoding="utf-8",
    )
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
        footnotes=footnotes,
    )


def _record_summary(
    rank: int,
    record: BenchmarkRecord,
    languages: tuple[str, ...],
) -> dict[str, Any]:
    summary = {
        "rank": rank,
        "runId": record.run_id,
        "compressionMethod": record.compression_method,
        "evidenceLevel": record.evidence_level,
        "evidenceLabel": evidence_short_label(record.evidence_level),
        "rankParameter": rank_parameter_label(record),
        "passAt1": round(record.pass_at_1, 4),
        "passAt5": round(record.pass_at_5, 4),
        "peakVramGb": record.peak_vram_gb,
        "durationSeconds": record.duration_seconds,
        "trainableParamCount": record.trainable_param_count,
    }
    for language in languages:
        key = _language_key(language)
        value = pass_at_1_for_language(record, language)
        summary[key] = round(value, 4) if value is not None else None
    return summary


def _build_markdown(
    ranked: list[BenchmarkRecord],
    warnings: tuple[str, ...],
    footnotes: tuple[ReportFootnote, ...],
    languages: tuple[str, ...],
) -> str:
    lang_headers = " | ".join(_language_header(language) for language in languages)
    lang_divider = " | ".join("---" for _ in languages)

    lines = [
        "# Wave 1 Method Ranking",
        "",
        "Comparative benchmark report (UC-005, BR-012, EVALUATION-METHOD.md).",
        "",
        "## Ranking rules",
        "",
        "1. Primary: aggregate Pass@1",
        "2. Tie-break: lower VRAM → lower train time → fewer trainable params",
        "3. BR-014: param delta >10% requires footnote",
        "4. L4 Speculative never ranked as best without label",
        "",
    ]

    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend(
        [
            "## Comparative table",
            "",
            f"| Rank | Method | Evidence | χ/rank | {lang_headers} | VRAM GB | Train s | Params |",
            f"|------|--------|----------|--------|{lang_divider}|---------|---------|--------|",
        ]
    )

    for index, record in enumerate(ranked, start=1):
        vram = "—" if record.peak_vram_gb is None else f"{record.peak_vram_gb:.1f}"
        duration = "—" if record.duration_seconds is None else f"{record.duration_seconds:.1f}"
        params = "—" if record.trainable_param_count is None else str(record.trainable_param_count)
        lang_cells = " | ".join(_format_language_cell(record, language) for language in languages)
        evidence = evidence_short_label(record.evidence_level)
        lines.append(
            f"| {index} | {record.compression_method} | {evidence} | "
            f"{rank_parameter_label(record)} | {lang_cells} | {vram} | {duration} | {params} |"
        )

    if footnotes:
        lines.extend(["", "## Footnotes", ""])
        for footnote in footnotes:
            lines.append(
                f"- **{footnote.compression_method}** (`{footnote.run_id}`): {footnote.reason}"
            )
        lines.append("")

    lines.extend(["", "## Tag bucket diagnostics", ""])
    for record in ranked:
        if not record.tag_buckets:
            continue
        lines.append(f"### {record.compression_method}")
        lines.append("")
        lines.append("| Tag | Tasks | Pass@1 | Pass@5 |")
        lines.append("|-----|-------|--------|--------|")
        for bucket in record.tag_buckets:
            lines.append(
                f"| {bucket.get('tag')} | {bucket.get('taskCount')} | "
                f"{bucket.get('passAt1', 0):.1%} | {bucket.get('passAt5', 0):.1%} |"
            )
        lines.append("")

    return "\n".join(lines)


def _language_header(language: str) -> str:
    mapping = {
        "JavaScript": "JS Pass@1",
        "HTML": "HTML Pass@1",
        "FreeMarker": "FMT Pass@1",
    }
    return mapping.get(language, f"{language} Pass@1")


def _language_key(language: str) -> str:
    mapping = {
        "JavaScript": "jsPassAt1",
        "HTML": "htmlPassAt1",
        "FreeMarker": "fmtPassAt1",
    }
    return mapping.get(language, f"{language}PassAt1")


def _format_language_cell(record: BenchmarkRecord, language: str) -> str:
    value = pass_at_1_for_language(record, language)
    if value is None:
        return "—"
    return f"{value:.1%}"


def _append_event(path: Path | None, event: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("timestamp", datetime.now(UTC).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
