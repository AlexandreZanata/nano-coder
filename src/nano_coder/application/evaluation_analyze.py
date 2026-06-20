"""Application service — enrich and analyze benchmark results (Phase 4)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.evaluation_metrics import (
    InferenceMetrics,
    ParamMatchFootnote,
    TagBucketSummary,
    evaluate_param_match,
    mock_inference_metrics,
    summarize_tag_buckets,
)
from nano_coder.domain.phase4_config import Phase4Config


@dataclass(frozen=True)
class EvaluationAnalysisResult:
    run_id: str
    evaluation_path: Path
    summary_path: Path
    tag_buckets: tuple[TagBucketSummary, ...]
    inference_metrics: InferenceMetrics | None
    param_match: ParamMatchFootnote | None


def analyze_benchmark_results(
    *,
    run_id: str,
    benchmark_root: Path,
    config: Phase4Config,
    anchor_param_count: int | None = None,
) -> EvaluationAnalysisResult:
    results_path = benchmark_root / run_id / "results.json"
    if not results_path.is_file():
        raise FileNotFoundError(f"benchmark results not found: {results_path}")

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    tasks = list(payload.get("tasks", []))
    compression_method = str(payload.get("compressionMethod", "Unknown"))

    tag_buckets: tuple[TagBucketSummary, ...] = ()
    if config.evaluation.include_tag_buckets:
        tag_buckets = summarize_tag_buckets(tasks)

    inference: InferenceMetrics | None = None
    if config.evaluation.include_inference_metrics:
        inference = mock_inference_metrics(
            compression_method=compression_method,
            mean_latency_ms_per_token=config.inference_mock.mean_latency_ms_per_token,
            throughput_tokens_per_sec=config.inference_mock.throughput_tokens_per_sec,
            base_model_size_mb=config.inference_mock.base_model_size_mb,
        )

    param_match: ParamMatchFootnote | None = None
    if config.evaluation.include_param_match_footnotes:
        param_match = evaluate_param_match(
            run_id=run_id,
            compression_method=compression_method,
            trainable_param_count=_optional_int(payload.get("trainableParamCount")),
            anchor_param_count=anchor_param_count,
            tolerance_percent=config.param_match_tolerance_percent,
        )

    evaluation_payload = _build_evaluation_payload(
        payload=payload,
        tag_buckets=tag_buckets,
        inference=inference,
        param_match=param_match,
        config=config,
    )

    output_dir = benchmark_root / run_id
    evaluation_path = output_dir / "evaluation.json"
    summary_path = output_dir / "evaluation-summary.md"
    evaluation_path.write_text(json.dumps(evaluation_payload, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(_build_evaluation_markdown(evaluation_payload), encoding="utf-8")

    return EvaluationAnalysisResult(
        run_id=run_id,
        evaluation_path=evaluation_path,
        summary_path=summary_path,
        tag_buckets=tag_buckets,
        inference_metrics=inference,
        param_match=param_match,
    )


def _build_evaluation_payload(
    *,
    payload: dict[str, Any],
    tag_buckets: tuple[TagBucketSummary, ...],
    inference: InferenceMetrics | None,
    param_match: ParamMatchFootnote | None,
    config: Phase4Config,
) -> dict[str, Any]:
    evaluation: dict[str, Any] = {
        "runId": payload.get("runId"),
        "compressionMethod": payload.get("compressionMethod"),
        "datasetVersion": payload.get("datasetVersion"),
        "heldOutTestSetVersion": payload.get("heldOutTestSetVersion"),
        "passAt1": payload.get("passAt1"),
        "passAt5": payload.get("passAt5"),
        "syntaxValidityRate": payload.get("syntaxValidityRate"),
        "byLanguage": payload.get("byLanguage"),
        "peakVramGb": payload.get("peakVramGb"),
        "durationSeconds": payload.get("durationSeconds"),
        "trainableParamCount": payload.get("trainableParamCount"),
        "analyzedAt": datetime.now(UTC).isoformat(),
    }

    if tag_buckets:
        evaluation["tagBuckets"] = [
            {
                "tag": bucket.tag,
                "taskCount": bucket.task_count,
                "passAt1": round(bucket.pass_at_1, 4),
                "passAt5": round(bucket.pass_at_5, 4),
            }
            for bucket in tag_buckets
        ]

    if inference is not None:
        evaluation["inference"] = {
            "meanLatencyMsPerToken": inference.mean_latency_ms_per_token,
            "throughputTokensPerSec": inference.throughput_tokens_per_sec,
            "modelSizeMb": inference.model_size_mb,
        }

    if param_match is not None:
        evaluation["paramMatch"] = {
            "matched": param_match.matched,
            "deltaPercent": param_match.delta_percent,
            "anchorParamCount": param_match.anchor_param_count,
            "trainableParamCount": param_match.trainable_param_count,
            "footnoteRequired": not param_match.matched,
        }

    evaluation["judgeSampleRate"] = config.evaluation.judge_sample_rate
    return evaluation


def _build_evaluation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Evaluation {payload['runId']}",
        "",
        f"- Method: {payload.get('compressionMethod')}",
        f"- Pass@1: **{payload.get('passAt1', 0):.1%}**",
        f"- Pass@5: **{payload.get('passAt5', 0):.1%}**",
        f"- Syntax validity: {payload.get('syntaxValidityRate', 0):.1%}",
        "",
    ]

    inference = payload.get("inference")
    if inference:
        lines.extend(
            [
                "## Inference cost",
                "",
                f"- Latency: {inference['meanLatencyMsPerToken']} ms/token",
                f"- Throughput: {inference['throughputTokensPerSec']} tokens/s",
                f"- Model size: {inference['modelSizeMb']} MB",
                "",
            ]
        )

    tag_buckets = payload.get("tagBuckets")
    if tag_buckets:
        lines.extend(
            [
                "## Tag buckets",
                "",
                "| Tag | Tasks | Pass@1 | Pass@5 |",
                "|-----|-------|--------|--------|",
            ]
        )
        for bucket in tag_buckets:
            lines.append(
                f"| {bucket['tag']} | {bucket['taskCount']} | "
                f"{bucket['passAt1']:.1%} | {bucket['passAt5']:.1%} |"
            )
        lines.append("")

    param_match = payload.get("paramMatch")
    if param_match and param_match.get("footnoteRequired"):
        lines.extend(
            [
                "## BR-014 footnote",
                "",
                f"Trainable params differ from anchor by "
                f"{param_match['deltaPercent']:.1f}% — comparison requires footnote.",
                "",
            ]
        )

    return "\n".join(lines)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)
