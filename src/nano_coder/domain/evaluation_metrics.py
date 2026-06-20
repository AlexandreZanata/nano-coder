"""Evaluation metrics and analysis (Phase 4, EVALUATION-METHOD.md, BR-014)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_TAG_LEVEL = re.compile(r"^L\d+")


@dataclass(frozen=True)
class TagBucketSummary:
    tag: str
    task_count: int
    pass_at_1: float
    pass_at_5: float


@dataclass(frozen=True)
class InferenceMetrics:
    mean_latency_ms_per_token: float
    throughput_tokens_per_sec: float
    model_size_mb: float


@dataclass(frozen=True)
class ParamMatchFootnote:
    run_id: str
    compression_method: str
    trainable_param_count: int
    anchor_param_count: int
    delta_percent: float
    matched: bool


def extract_tag_bucket(task: dict[str, Any]) -> str:
    for tag in task.get("tags", []):
        text = str(tag)
        if _TAG_LEVEL.match(text):
            return text
    return "untagged"


def summarize_tag_buckets(tasks: list[dict[str, Any]]) -> tuple[TagBucketSummary, ...]:
    buckets: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        bucket = extract_tag_bucket(task)
        buckets.setdefault(bucket, []).append(task)

    summaries: list[TagBucketSummary] = []
    for tag, bucket_tasks in sorted(buckets.items()):
        passed_at_1 = sum(1 for task in bucket_tasks if task.get("passAt1"))
        passed_at_k = sum(1 for task in bucket_tasks if task.get("passAt5"))
        count = len(bucket_tasks)
        summaries.append(
            TagBucketSummary(
                tag=tag,
                task_count=count,
                pass_at_1=passed_at_1 / count if count else 0.0,
                pass_at_5=passed_at_k / count if count else 0.0,
            )
        )
    return tuple(summaries)


def mock_inference_metrics(
    *,
    compression_method: str,
    mean_latency_ms_per_token: float,
    throughput_tokens_per_sec: float,
    base_model_size_mb: float,
) -> InferenceMetrics:
    size_mb = base_model_size_mb
    latency = mean_latency_ms_per_token
    throughput = throughput_tokens_per_sec

    if compression_method == "QLoRA":
        size_mb = base_model_size_mb * 0.55
        latency *= 1.12
        throughput *= 0.92
    elif compression_method == "FewShot":
        size_mb = base_model_size_mb
        latency *= 0.95
        throughput *= 1.05

    return InferenceMetrics(
        mean_latency_ms_per_token=round(latency, 2),
        throughput_tokens_per_sec=round(throughput, 2),
        model_size_mb=round(size_mb, 2),
    )


def evaluate_param_match(
    *,
    run_id: str,
    compression_method: str,
    trainable_param_count: int | None,
    anchor_param_count: int | None,
    tolerance_percent: float,
) -> ParamMatchFootnote | None:
    if trainable_param_count is None or anchor_param_count is None or anchor_param_count == 0:
        return None
    delta_percent = abs(trainable_param_count - anchor_param_count) / anchor_param_count * 100
    return ParamMatchFootnote(
        run_id=run_id,
        compression_method=compression_method,
        trainable_param_count=trainable_param_count,
        anchor_param_count=anchor_param_count,
        delta_percent=round(delta_percent, 2),
        matched=delta_percent <= tolerance_percent,
    )
