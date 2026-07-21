"""GIVEN/WHEN/THEN — domain entity contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nano_orchestrator.domain.entities import (
    JudgeVerdict,
    MicroTask,
    TargetLanguage,
    WorkerResponse,
    WorkerRole,
)
from nano_orchestrator.domain.rubric import score_verdict
from nano_orchestrator.domain.task_splitter import MAX_ACTIVE_WORKERS, assert_worker_cap


def test_given_valid_microtask_when_created_then_ok() -> None:
    task = MicroTask(
        id="js-001",
        role=WorkerRole.CODER,
        language=TargetLanguage.JAVASCRIPT,
        prompt="Export a pure filterValues function",
        acceptance=["syntax_valid"],
        max_tokens=256,
    )
    assert task.language is TargetLanguage.JAVASCRIPT


def test_given_invalid_language_when_created_then_rejects() -> None:
    with pytest.raises(ValidationError):
        MicroTask(
            id="bad-001",
            role=WorkerRole.CODER,
            language="python",  # type: ignore[arg-type]
            prompt="x",
            acceptance=["syntax_valid"],
        )


def test_given_confidence_out_of_range_when_created_then_rejects() -> None:
    with pytest.raises(ValidationError):
        WorkerResponse(
            task_id="js-001",
            code="export const x = 1;",
            confidence=1.5,
            latency_ms=10,
            tokens_used=20,
        )


def test_given_six_tasks_when_assert_cap_then_raises() -> None:
    tasks = [
        MicroTask(
            id=f"t-{i}",
            role=WorkerRole.CODER,
            language=TargetLanguage.HTML,
            prompt="p",
            acceptance=["syntax_valid"],
        )
        for i in range(MAX_ACTIVE_WORKERS + 1)
    ]
    with pytest.raises(ValueError, match="worker cap"):
        assert_worker_cap(tasks)


def test_given_sandbox_fail_when_score_then_retry_recommended() -> None:
    verdict: JudgeVerdict = score_verdict(
        task_id="js-001",
        sandbox_checks={"syntax": False},
        contract_ok=True,
        llm_secondary_score=1.0,
        retry_count=0,
    )
    assert verdict.passed is False
    assert verdict.retry_recommended is True
