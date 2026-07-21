"""Orchestrate use case — Application layer (LLM calls via ports only)."""

from __future__ import annotations

from nano_orchestrator.domain.entities import MicroTask
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.domain.task_splitter import validate_microtasks
from nano_orchestrator.ports.llm_backend import LlmBackend


class OrchestrateUseCase:
    """Decompose a user request into MicroTasks via the orchestrator model."""

    def __init__(self, backend: LlmBackend) -> None:
        self._backend = backend

    def decompose(self, user_request: str) -> Result[list[MicroTask], str]:
        # Phase 2: call backend with structured prompt, parse JSON into MicroTask[].
        # Stub returns Err until wired — keeps boundary honest.
        if not user_request.strip():
            return Err("empty_request")
        _ = self._backend  # reserved for Phase 2 wiring
        return Err("not_implemented: wire LlmBackend + JSON parse in Phase 2")


def enforce_cap(tasks: list[MicroTask]) -> Result[list[MicroTask], str]:
    try:
        return Ok(validate_microtasks(tasks))
    except ValueError as exc:
        return Err(str(exc))
