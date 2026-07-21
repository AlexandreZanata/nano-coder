"""Retry policy — hard cap to prevent cascade latency."""

from __future__ import annotations

from nano_orchestrator.domain.entities import JudgeVerdict
from nano_orchestrator.domain.rubric import MAX_RETRIES


def should_retry(verdict: JudgeVerdict, retry_count: int) -> bool:
    return verdict.retry_recommended and retry_count < MAX_RETRIES


def escalate_to_human(verdict: JudgeVerdict, retry_count: int) -> bool:
    return (not verdict.passed) and retry_count >= MAX_RETRIES
