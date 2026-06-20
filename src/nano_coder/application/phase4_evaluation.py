"""Application service — Phase 4 evaluation orchestrator (UC-004, Part 3)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.application.evaluation_analyze import analyze_benchmark_results
from nano_coder.domain.evaluation_readiness import verify_evaluation_readiness
from nano_coder.domain.experiment_config import format_run_id, load_phase3_config
from nano_coder.domain.phase4_config import Phase4Config


@dataclass(frozen=True)
class Phase4EvaluationEntry:
    run_id: str
    compression_method: str
    pass_at_1: float
    evaluation_path: Path


@dataclass
class Phase4EvaluationResult:
    profile: str
    benchmark_run_ids: tuple[str, ...]
    failed: bool = False
    entries: list[Phase4EvaluationEntry] = field(default_factory=list)
    readiness_passed: bool = True


def run_phase4_evaluation(
    *,
    config: Phase4Config,
    project_root: Path,
    profile: str | None = None,
    benchmark_run_ids: list[str] | None = None,
    phase3_config_path: Path | None = None,
) -> Phase4EvaluationResult:
    resolved_profile = profile or config.profile
    paths = _resolve_paths(project_root, config)
    run_ids = benchmark_run_ids or _load_run_ids_from_phase3(
        project_root,
        config,
        profile=resolved_profile,
        phase3_config_path=phase3_config_path or paths["phase3_config"],
    )

    result = Phase4EvaluationResult(
        profile=resolved_profile,
        benchmark_run_ids=tuple(run_ids),
    )

    readiness = verify_evaluation_readiness(
        held_out_root=paths["held_out"],
        benchmark_root=paths["benchmarks"],
        benchmark_run_ids=run_ids,
        expected_test_set_version=config.held_out_test_set_version,
    )
    result.readiness_passed = readiness.passed
    if not readiness.passed:
        result.failed = True
        _write_report(result, paths, readiness_checks=readiness.checks)
        return result

    anchor_param_count = _resolve_anchor_param_count(
        paths["benchmarks"],
        config,
        profile=resolved_profile,
        phase3_config_path=phase3_config_path or paths["phase3_config"],
    )

    for run_id in run_ids:
        try:
            payload = json.loads((paths["benchmarks"] / run_id / "results.json").read_text())
            analysis = analyze_benchmark_results(
                run_id=run_id,
                benchmark_root=paths["benchmarks"],
                config=config,
                anchor_param_count=anchor_param_count,
            )
            result.entries.append(
                Phase4EvaluationEntry(
                    run_id=run_id,
                    compression_method=str(payload.get("compressionMethod", "Unknown")),
                    pass_at_1=float(payload.get("passAt1", 0.0)),
                    evaluation_path=analysis.evaluation_path,
                )
            )
        except Exception:
            result.failed = True

    _write_report(result, paths, readiness_checks=readiness.checks)
    return result


def _load_run_ids_from_phase3(
    project_root: Path,
    config: Phase4Config,
    *,
    profile: str,
    phase3_config_path: Path,
) -> list[str]:
    report_path = project_root / config.phase3_report
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        return [item["benchmarkRunId"] for item in report.get("experiments", [])]

    phase3 = load_phase3_config(phase3_config_path)
    return [
        format_run_id(spec.run_id_templates["benchmark"], profile=profile)
        for spec in phase3.experiments.values()
    ]


def _resolve_anchor_param_count(
    benchmark_root: Path,
    config: Phase4Config,
    *,
    profile: str,
    phase3_config_path: Path,
) -> int | None:
    phase3 = load_phase3_config(phase3_config_path)
    anchor_spec = next(
        (
            spec
            for spec in phase3.experiments.values()
            if spec.compression_method.value == config.anchor_compression_method
        ),
        None,
    )
    if anchor_spec is None:
        return None

    train_run_id = format_run_id(anchor_spec.run_id_templates["train"], profile=profile)
    bench_run_id = format_run_id(anchor_spec.run_id_templates["benchmark"], profile=profile)

    for run_id in (bench_run_id,):
        results_path = benchmark_root / run_id / "results.json"
        if results_path.is_file():
            payload = json.loads(results_path.read_text(encoding="utf-8"))
            count = payload.get("trainableParamCount")
            if count is not None:
                return int(count)

    checkpoint_manifest = (
        benchmark_root.parent / "checkpoints" / train_run_id / "checkpoint-manifest.json"
    )
    if checkpoint_manifest.is_file():
        payload = json.loads(checkpoint_manifest.read_text(encoding="utf-8"))
        count = payload.get("trainableParamCount")
        if count is not None:
            return int(count)
    return None


def _resolve_paths(project_root: Path, config: Phase4Config) -> dict[str, Path]:
    return {
        "held_out": project_root / "data" / "benchmarks" / "held-out-v1",
        "benchmarks": project_root / "data" / "benchmarks",
        "checkpoints": project_root / "data" / "checkpoints",
        "review": project_root / ".local" / "review",
        "phase3_config": project_root / "config" / "phase3-v1.yaml",
        "smoke_report": project_root / config.smoke_train_report,
    }


def _write_report(
    result: Phase4EvaluationResult,
    paths: dict[str, Path],
    *,
    readiness_checks: tuple,
) -> None:
    report_path = paths["review"] / "phase4-evaluation-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": result.profile,
        "failed": result.failed,
        "readinessPassed": result.readiness_passed,
        "benchmarkRunIds": list(result.benchmark_run_ids),
        "completedAt": datetime.now(UTC).isoformat(),
        "readinessChecks": [
            {"name": check.name, "passed": check.passed, "detail": check.detail}
            for check in readiness_checks
        ],
        "evaluations": [
            {
                "runId": entry.run_id,
                "compressionMethod": entry.compression_method,
                "passAt1": entry.pass_at_1,
                "evaluationPath": str(entry.evaluation_path),
            }
            for entry in result.entries
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    summary_path = paths["review"] / "evaluation-results-summary.md"
    summary_path.write_text(_build_operator_summary(payload), encoding="utf-8")


def _build_operator_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Evaluation Results Summary",
        "",
        f"Profile: **{payload['profile']}**",
        "",
        "| Method | Pass@1 | Evaluation |",
        "|--------|--------|------------|",
    ]
    for entry in payload.get("evaluations", []):
        lines.append(
            f"| {entry['compressionMethod']} | {entry['passAt1']:.1%} | "
            f"`{entry['evaluationPath']}` |"
        )
    lines.append("")
    return "\n".join(lines)
