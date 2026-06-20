"""Unit tests for TrainingRun state machine."""

from __future__ import annotations

import pytest

from nano_coder.domain.training_run import (
    InvalidTrainingTransition,
    TrainingRun,
    TrainingRunState,
)


def test_training_run_happy_path():
    run = TrainingRun("train-001", "ds-2026-06-20-js-v1")
    run.transition(TrainingRunState.RUNNING)
    run.transition(TrainingRunState.COMPLETED)
    assert run.state is TrainingRunState.COMPLETED


def test_training_run_rejects_invalid_transition():
    run = TrainingRun("train-001", "ds-2026-06-20-js-v1")
    with pytest.raises(InvalidTrainingTransition):
        run.transition(TrainingRunState.COMPLETED)
