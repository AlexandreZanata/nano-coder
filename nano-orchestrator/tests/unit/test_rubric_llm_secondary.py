"""Rubric: LLM secondary never sole pass (T-044)."""

from __future__ import annotations

from nano_orchestrator.domain.entities import JudgeVerdict
from nano_orchestrator.domain.rubric import (
    PASS_THRESHOLD,
    WEIGHT_LLM_SECONDARY,
    WEIGHT_SANDBOX,
    score_verdict,
)


def test_given_sandbox_fail_and_llm_perfect_when_score_then_passed_false() -> None:
    """DoD T-044: sandbox fails + LLM=1.0 still passed=false."""
    verdict: JudgeVerdict = score_verdict(
        task_id="js-001",
        sandbox_checks={"syntax": False},
        contract_ok=True,
        llm_secondary_score=1.0,
        retry_count=0,
    )
    assert verdict.passed is False
    assert verdict.score < PASS_THRESHOLD
    # Sandbox weight alone is enough that LLM secondary cannot flip the gate.
    assert WEIGHT_SANDBOX > (1.0 - PASS_THRESHOLD)
    assert WEIGHT_LLM_SECONDARY < PASS_THRESHOLD


def test_given_sandbox_and_contract_ok_when_llm_zero_then_still_can_pass() -> None:
    verdict = score_verdict(
        task_id="js-002",
        sandbox_checks={"syntax": True},
        contract_ok=True,
        llm_secondary_score=0.0,
        retry_count=0,
    )
    assert verdict.passed is True
    assert verdict.score >= PASS_THRESHOLD


def test_given_empty_checks_when_score_then_not_passed() -> None:
    verdict = score_verdict(
        task_id="js-003",
        sandbox_checks={},
        contract_ok=True,
        llm_secondary_score=1.0,
        retry_count=0,
    )
    assert verdict.passed is False
