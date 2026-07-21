"""Pure task-splitting helpers — no LLM calls here."""

from __future__ import annotations

from nano_orchestrator.domain.entities import MicroTask

MAX_ACTIVE_WORKERS = 5


def assert_worker_cap(tasks: list[MicroTask]) -> None:
    if len(tasks) > MAX_ACTIVE_WORKERS:
        raise ValueError(
            f"worker cap exceeded: {len(tasks)} > {MAX_ACTIVE_WORKERS} (ASI08)"
        )


def validate_microtasks(tasks: list[MicroTask]) -> list[MicroTask]:
    """Re-validate list (Pydantic already ran); enforce orchestration caps."""
    assert_worker_cap(tasks)
    return tasks
