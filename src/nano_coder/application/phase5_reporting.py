"""Application service — Phase 5 Wave 1 reporting orchestrator (Part 5)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nano_coder.application.report_export import ReportExportResult, export_benchmark_report
from nano_coder.domain.experiment_config import format_run_id, load_phase3_config
from nano_coder.domain.phase5_config import Phase5Config


@dataclass(frozen=True)
class Phase5ReportResult:
    wave: int
    profile: str
    run_ids: tuple[str, ...]
    export: ReportExportResult
    failed: bool


def run_phase5_wave1_report(
    *,
    config: Phase5Config,
    project_root: Path,
    profile: str | None = None,
    run_ids: list[str] | None = None,
    allow_mixed: bool = False,
) -> Phase5ReportResult:
    resolved_profile = profile or config.profile
    benchmark_root = project_root / "data" / "benchmarks"
    events_log = project_root / "data" / "events" / "events.jsonl"

    resolved_run_ids = run_ids or _resolve_run_ids(project_root, config, profile=resolved_profile)
    if len(resolved_run_ids) < 2:
        raise ValueError("Phase 5 ranking requires at least two benchmark run ids")

    output_md = project_root / config.output_markdown
    export = export_benchmark_report(
        run_ids=resolved_run_ids,
        benchmark_root=benchmark_root,
        output_path=output_md,
        languages=config.languages,
        tie_breakers=config.tie_breakers,
        allow_mixed=allow_mixed,
        events_log=events_log,
    )

    _write_phase5_report(project_root, config, resolved_profile, export, resolved_run_ids)
    return Phase5ReportResult(
        wave=config.wave,
        profile=resolved_profile,
        run_ids=tuple(resolved_run_ids),
        export=export,
        failed=False,
    )


def _resolve_run_ids(
    project_root: Path,
    config: Phase5Config,
    *,
    profile: str,
) -> list[str]:
    phase4_path = project_root / config.phase4_report
    if phase4_path.is_file():
        report = json.loads(phase4_path.read_text(encoding="utf-8"))
        run_ids = [entry["runId"] for entry in report.get("evaluations", [])]
        if run_ids:
            return run_ids

    phase3_path = project_root / config.phase3_report
    if phase3_path.is_file():
        report = json.loads(phase3_path.read_text(encoding="utf-8"))
        run_ids = [entry["benchmarkRunId"] for entry in report.get("experiments", [])]
        if run_ids:
            return run_ids

    phase3 = load_phase3_config(project_root / "config" / "phase3-v1.yaml")
    return [
        format_run_id(spec.run_id_templates["benchmark"], profile=profile)
        for spec in phase3.experiments.values()
    ]


def _write_phase5_report(
    project_root: Path,
    config: Phase5Config,
    profile: str,
    export: ReportExportResult,
    run_ids: list[str],
) -> None:
    report_path = project_root / ".local" / "review" / "phase5-wave1-ranking-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "wave": config.wave,
        "profile": profile,
        "runIds": run_ids,
        "outputMarkdown": str(export.output_path),
        "outputJson": str(export.summary_path),
        "recordCount": export.record_count,
        "warnings": list(export.warnings),
        "footnotes": [
            {
                "runId": footnote.run_id,
                "compressionMethod": footnote.compression_method,
                "reason": footnote.reason,
            }
            for footnote in export.footnotes
        ],
        "completedAt": datetime.now(UTC).isoformat(),
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    json_output = project_root / config.output_json
    json_output.parent.mkdir(parents=True, exist_ok=True)
    if export.summary_path.is_file():
        json_output.write_text(export.summary_path.read_text(encoding="utf-8"), encoding="utf-8")
