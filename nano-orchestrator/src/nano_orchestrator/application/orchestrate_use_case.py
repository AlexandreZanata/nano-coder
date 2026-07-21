"""Orchestrate use case — decompose user request into MicroTasks."""

from __future__ import annotations

from nano_orchestrator.application.codegen_prompts import build_orchestrator_prompt
from nano_orchestrator.domain.entities import MicroTask
from nano_orchestrator.domain.microtask_parser import parse_microtasks_json
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.domain.task_splitter import validate_microtasks
from nano_orchestrator.ports.llm_backend import LlmBackend


class OrchestrateUseCase:
    """Decompose a user request into MicroTasks via the orchestrator model."""

    def __init__(self, backend: LlmBackend, *, max_tokens: int = 768) -> None:
        self._backend = backend
        self._max_tokens = max_tokens

    def decompose(self, user_request: str) -> Result[list[MicroTask], str]:
        if not user_request.strip():
            return Err("empty_request")
        prompt = build_orchestrator_prompt(user_request)
        gen = self._backend.generate(prompt, max_tokens=self._max_tokens)
        if gen.is_err():
            return Err(gen.error)  # type: ignore[union-attr]
        return parse_microtasks_json(gen.value)  # type: ignore[union-attr]


def enforce_cap(tasks: list[MicroTask]) -> Result[list[MicroTask], str]:
    try:
        return Ok(validate_microtasks(tasks))
    except ValueError as exc:
        return Err(str(exc))
