"""Unit tests for benchmark run state machine."""

from __future__ import annotations

import pytest

from nano_coder.domain.benchmark_run import (
    BenchmarkRun,
    BenchmarkRunState,
    InvalidBenchmarkTransition,
)


def test_benchmark_run_happy_path():
    run = BenchmarkRun("bench-001", "train-001")
    run.transition(BenchmarkRunState.RUNNING)
    run.transition(BenchmarkRunState.COMPLETED)
    assert run.state is BenchmarkRunState.COMPLETED


def test_benchmark_run_rejects_invalid_transition():
    run = BenchmarkRun("bench-001", "train-001")
    with pytest.raises(InvalidBenchmarkTransition):
        run.transition(BenchmarkRunState.COMPLETED)
