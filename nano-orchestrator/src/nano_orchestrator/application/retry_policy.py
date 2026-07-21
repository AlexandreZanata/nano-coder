"""Retry policy — hard cap + adaptive budget from confidence (Phase 5)."""

from __future__ import annotations

from nano_orchestrator.domain.entities import JudgeVerdict
from nano_orchestrator.domain.rubric import MAX_RETRIES


def retry_budget(
    confidence: float,
    *,
    max_budget: int = MAX_RETRIES,
    high_confidence_min: float = 0.8,
    medium_confidence_min: float = 0.5,
) -> int:
    """Map worker confidence → allowed retries in [0, max_budget] (cap 2)."""
    cap = min(max(0, max_budget), MAX_RETRIES)
    conf = max(0.0, min(1.0, float(confidence)))
    if conf >= high_confidence_min:
        return 0
    if conf >= medium_confidence_min:
        return min(1, cap)
    return cap


def should_retry(
    verdict: JudgeVerdict,
    retry_count: int,
    *,
    budget: int | None = None,
) -> bool:
    limit = MAX_RETRIES if budget is None else max(0, min(budget, MAX_RETRIES))
    return verdict.retry_recommended and retry_count < limit


def escalate_to_human(
    verdict: JudgeVerdict,
    retry_count: int,
    *,
    budget: int | None = None,
) -> bool:
    limit = MAX_RETRIES if budget is None else max(0, min(budget, MAX_RETRIES))
    return (not verdict.passed) and retry_count >= limit
