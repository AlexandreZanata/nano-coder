"""Unit tests for evaluation metrics domain."""

from __future__ import annotations

from nano_coder.domain.evaluation_metrics import (
    evaluate_param_match,
    extract_tag_bucket,
    mock_inference_metrics,
    summarize_tag_buckets,
)


def test_extract_tag_bucket_reads_level_tag():
    task = {"tags": ["held-out", "L3-composite"]}
    assert extract_tag_bucket(task) == "L3-composite"


def test_summarize_tag_buckets_groups_tasks():
    tasks = [
        {"tags": ["L3-composite"], "passAt1": True, "passAt5": True},
        {"tags": ["L3-composite"], "passAt1": False, "passAt5": True},
        {"tags": ["L2-standard"], "passAt1": True, "passAt5": True},
    ]
    summaries = summarize_tag_buckets(tasks)
    assert len(summaries) == 2
    l3 = next(item for item in summaries if item.tag == "L3-composite")
    assert l3.pass_at_1 == 0.5


def test_evaluate_param_match_flags_large_delta():
    footnote = evaluate_param_match(
        run_id="bench-dora-001",
        compression_method="DoRA",
        trainable_param_count=1200,
        anchor_param_count=1000,
        tolerance_percent=10,
    )
    assert footnote is not None
    assert footnote.matched is False


def test_mock_inference_metrics_qlora_smaller_model():
    metrics = mock_inference_metrics(
        compression_method="QLoRA",
        mean_latency_ms_per_token=10.0,
        throughput_tokens_per_sec=100.0,
        base_model_size_mb=1000.0,
    )
    assert metrics.model_size_mb < 1000.0
