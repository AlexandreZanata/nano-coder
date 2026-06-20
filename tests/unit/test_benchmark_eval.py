"""Unit tests for benchmark evaluation domain."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_coder.domain.benchmark_eval import (
    HeldOutVersionMismatch,
    load_all_held_out_tasks,
    summarize_benchmark,
    summarize_language_benchmark,
    validate_test_set_version,
)
from nano_coder.domain.target_language import TargetLanguage

ROOT = Path(__file__).resolve().parents[2]


def test_validate_test_set_version_accepts_held_out_v1():
    manifest = validate_test_set_version(
        ROOT / "data" / "benchmarks" / "held-out-v1",
        expected_version="held-out-v1",
    )
    assert manifest["taskCount"] == 150


def test_validate_test_set_version_rejects_mismatch():
    with pytest.raises(HeldOutVersionMismatch):
        validate_test_set_version(
            ROOT / "data" / "benchmarks" / "held-out-v1",
            expected_version="held-out-v2",
        )


def test_load_all_held_out_tasks_has_three_languages():
    tasks = load_all_held_out_tasks(ROOT / "data" / "benchmarks" / "held-out-v1")
    assert len(tasks) == 3
    assert len(tasks[TargetLanguage.JAVASCRIPT]) == 50


def test_summarize_benchmark_weighted_average():
    summaries = [
        summarize_language_benchmark(
            language=TargetLanguage.JAVASCRIPT,
            pass_at_1_hits=40,
            pass_at_k_hits=45,
            syntax_valid_hits=48,
            task_count=50,
        ),
        summarize_language_benchmark(
            language=TargetLanguage.HTML,
            pass_at_1_hits=30,
            pass_at_k_hits=35,
            syntax_valid_hits=40,
            task_count=50,
        ),
    ]
    summary = summarize_benchmark(summaries, held_out_test_set_version="held-out-v1")
    assert summary.task_count == 100
    assert summary.pass_at_1 == 0.7
