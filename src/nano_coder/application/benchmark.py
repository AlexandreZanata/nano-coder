"""Application service — held-out benchmark (UC-004, Phase 2)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.benchmark_config import BenchmarkConfig
from nano_coder.domain.benchmark_eval import (
    BenchmarkSummary,
    evaluate_task_pass_at_k,
    load_all_held_out_tasks,
    summarize_benchmark,
    summarize_language_benchmark,
    validate_test_set_version,
)
from nano_coder.domain.benchmark_run import BenchmarkRun, BenchmarkRunState
from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.smoke_eval import evaluate_smoke_task
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.mock_trainer import (
    load_checkpoint_manifest,
    mock_generate_response,
    mock_pass_ratio,
)


@dataclass(frozen=True)
class BenchmarkResult:
    run_id: str
    checkpoint_run_id: str
    benchmark_state: BenchmarkRunState
    summary: BenchmarkSummary
    results_path: Path
    summary_path: Path


def run_benchmark(
    *,
    run_id: str,
    checkpoint_dir: Path,
    held_out_root: Path,
    output_root: Path,
    config: BenchmarkConfig,
    test_set_version: str | None = None,
    events_log: Path | None = None,
    dry_run: bool = True,
    max_tasks_per_language: int | None = None,
) -> BenchmarkResult:
    expected_version = test_set_version or config.held_out_test_set_version
    validate_test_set_version(held_out_root, expected_version=expected_version)
    checkpoint_manifest = load_checkpoint_manifest(checkpoint_dir)
    checkpoint_run_id = str(checkpoint_manifest["runId"])
    method = CompressionMethod(checkpoint_manifest.get("compressionMethod", "LoRA"))
    pass_ratio = mock_pass_ratio(method)
    task_limit = max_tasks_per_language
    if not dry_run and task_limit is None:
        task_limit = config.real_max_tasks_per_language

    run = BenchmarkRun(run_id, checkpoint_run_id)
    run.transition(BenchmarkRunState.RUNNING)
    _append_event(
        events_log,
        {
            "event": "BenchmarkRunStarted",
            "runId": run_id,
            "checkpointRunId": checkpoint_run_id,
            "heldOutTestSetVersion": expected_version,
        },
    )

    tasks_by_language = load_all_held_out_tasks(held_out_root)
    language_summaries = []
    task_results: list[dict[str, Any]] = []

    try:
        for language, tasks in tasks_by_language.items():
            selected_tasks = tasks[:task_limit] if task_limit else tasks
            pass_at_1_hits = 0
            pass_at_k_hits = 0
            syntax_valid_hits = 0
            for task_index, task in enumerate(selected_tasks):
                samples = _generate_task_samples(
                    task=task,
                    language=language,
                    task_index=task_index,
                    checkpoint_dir=checkpoint_dir,
                    dry_run=dry_run,
                    pass_ratio=pass_ratio,
                    samples_per_task=config.samples_per_task,
                )
                pass_at_1, pass_at_k = evaluate_task_pass_at_k(
                    task,
                    language=language,
                    samples=samples,
                )
                if pass_at_1:
                    pass_at_1_hits += 1
                if pass_at_k:
                    pass_at_k_hits += 1
                if evaluate_smoke_task(task, samples[0], language=language).passed or _syntax_valid(
                    language,
                    samples[0],
                ):
                    syntax_valid_hits += 1

                task_results.append(
                    {
                        "taskId": task.get("id"),
                        "targetLanguage": language.value,
                        "tags": list(task.get("tags", [])),
                        "passAt1": pass_at_1,
                        "passAt5": pass_at_k,
                    }
                )

            language_summaries.append(
                summarize_language_benchmark(
                    language=language,
                    pass_at_1_hits=pass_at_1_hits,
                    pass_at_k_hits=pass_at_k_hits,
                    syntax_valid_hits=syntax_valid_hits,
                    task_count=len(selected_tasks),
                )
            )
    finally:
        if not dry_run:
            from nano_coder.infrastructure.hf_student_inference import clear_inference_cache

            clear_inference_cache()

    summary = summarize_benchmark(
        language_summaries,
        held_out_test_set_version=expected_version,
    )
    run.transition(BenchmarkRunState.COMPLETED)

    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.json"
    summary_path = output_dir / "summary.md"

    results_payload = _build_results_payload(
        run_id=run_id,
        checkpoint_manifest=checkpoint_manifest,
        summary=summary,
        task_results=task_results,
        dry_run=dry_run,
    )
    results_path.write_text(json.dumps(results_payload, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(_build_summary_markdown(results_payload), encoding="utf-8")

    _append_event(
        events_log,
        {
            "event": "BenchmarkRunCompleted",
            "runId": run_id,
            "passAt1": round(summary.pass_at_1, 4),
            "passAt5": round(summary.pass_at_5, 4),
        },
    )

    return BenchmarkResult(
        run_id=run_id,
        checkpoint_run_id=checkpoint_run_id,
        benchmark_state=run.state,
        summary=summary,
        results_path=results_path,
        summary_path=summary_path,
    )


def _generate_task_samples(
    *,
    task: dict[str, Any],
    language: TargetLanguage,
    task_index: int,
    checkpoint_dir: Path,
    dry_run: bool,
    pass_ratio: float,
    samples_per_task: int,
) -> list[str]:
    if dry_run:
        return [
            mock_generate_response(
                task,
                language=language,
                task_index=task_index,
                pass_ratio=pass_ratio,
                sample_index=sample_index,
            )
            for sample_index in range(samples_per_task)
        ]

    from nano_coder.infrastructure.hf_student_inference import generate_student_samples

    instruction = str(task.get("instruction", "")).strip()
    return generate_student_samples(
        checkpoint_dir,
        instruction=instruction,
        num_samples=samples_per_task,
    )


def _syntax_valid(language: TargetLanguage, generated_code: str) -> bool:
    from nano_coder.infrastructure.syntax_validators import SyntaxValidationError, validate_syntax

    try:
        validate_syntax(language, generated_code)
        return True
    except SyntaxValidationError:
        return False


def _build_results_payload(
    *,
    run_id: str,
    checkpoint_manifest: dict[str, Any],
    summary: BenchmarkSummary,
    task_results: list[dict[str, Any]],
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "runId": run_id,
        "checkpointRunId": checkpoint_manifest.get("runId"),
        "compressionMethod": checkpoint_manifest.get("compressionMethod"),
        "datasetVersion": checkpoint_manifest.get("datasetVersion"),
        "studentModel": checkpoint_manifest.get("studentModel"),
        "heldOutTestSetVersion": summary.held_out_test_set_version,
        "dryRun": dry_run,
        "taskCount": summary.task_count,
        "passAt1": round(summary.pass_at_1, 4),
        "passAt5": round(summary.pass_at_5, 4),
        "syntaxValidityRate": round(summary.syntax_validity_rate, 4),
        "byLanguage": {
            item.language.value: {
                "taskCount": item.task_count,
                "passAt1": round(item.pass_at_1, 4),
                "passAt5": round(item.pass_at_5, 4),
                "syntaxValidityRate": round(item.syntax_validity_rate, 4),
            }
            for item in summary.by_language
        },
        "peakVramGb": checkpoint_manifest.get("peakVramGb"),
        "durationSeconds": checkpoint_manifest.get("durationSeconds"),
        "trainableParamCount": checkpoint_manifest.get("trainableParamCount"),
        "tasks": task_results,
        "completedAt": datetime.now(UTC).isoformat(),
    }


def _build_summary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Benchmark {payload['runId']}",
        "",
        f"- Checkpoint: `{payload['checkpointRunId']}`",
        f"- Method: {payload.get('compressionMethod')}",
        f"- Dataset: {payload.get('datasetVersion')}",
        f"- Test set: {payload['heldOutTestSetVersion']}",
        "",
        "## Aggregate",
        "",
        f"- Pass@1: **{payload['passAt1']:.1%}**",
        f"- Pass@5: **{payload['passAt5']:.1%}**",
        f"- Syntax validity: {payload['syntaxValidityRate']:.1%}",
        "",
        "## By language",
        "",
        "| Language | Pass@1 | Pass@5 | Syntax |",
        "|----------|--------|--------|--------|",
    ]
    for language, metrics in payload["byLanguage"].items():
        lines.append(
            f"| {language} | {metrics['passAt1']:.1%} | {metrics['passAt5']:.1%} | "
            f"{metrics['syntaxValidityRate']:.1%} |"
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
