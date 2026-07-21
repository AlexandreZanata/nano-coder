"""Route MicroTasks to locked worker model IDs by language."""

from __future__ import annotations

from dataclasses import dataclass

from nano_orchestrator.domain.entities import MicroTask, TargetLanguage, WorkerResponse
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.application.codegen_prompts import build_worker_prompt, extract_code
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter


@dataclass(frozen=True, slots=True)
class WorkerRouting:
    """Locked winners from Phase 1 bake-off."""

    javascript: str = "qwen25-coder-0.5b"
    html: str = "qwen25-coder-0.5b"
    freemarker: str = "smollm2-360m"
    default: str = "qwen25-coder-0.5b"

    def model_for(self, language: TargetLanguage) -> str:
        if language is TargetLanguage.JAVASCRIPT:
            return self.javascript
        if language is TargetLanguage.HTML:
            return self.html
        if language is TargetLanguage.FREEMARKER:
            return self.freemarker
        return self.default


def group_tasks_by_model(
    tasks: list[MicroTask], routing: WorkerRouting
) -> dict[str, list[MicroTask]]:
    grouped: dict[str, list[MicroTask]] = {}
    for task in tasks:
        model_id = routing.model_for(task.language)
        grouped.setdefault(model_id, []).append(task)
    return grouped


class WorkerDispatchUseCase:
    def __init__(self, adapter: LlamaCppAdapter) -> None:
        self._adapter = adapter

    def run_task(self, task: MicroTask) -> Result[WorkerResponse, str]:
        prompt = build_worker_prompt(task)
        gen = self._adapter.generate_detailed(prompt, max_tokens=task.max_tokens)
        if gen.is_err():
            return Err(gen.error)  # type: ignore[union-attr]
        result = gen.value  # type: ignore[union-attr]
        code = extract_code(result.text, task.language)
        tokens = result.tokens_predicted or max(1, len(code.split()))
        return Ok(
            WorkerResponse(
                task_id=task.id,
                code=code,
                confidence=0.5,
                notes=None,
                latency_ms=result.latency_ms,
                tokens_used=tokens,
            )
        )
