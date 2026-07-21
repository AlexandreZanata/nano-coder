"""Judge use case — sandbox first, optional LLM secondary."""

from __future__ import annotations

from nano_orchestrator.domain.entities import JudgeVerdict, MicroTask, WorkerResponse
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.domain.rubric import response_within_token_budget, score_verdict
from nano_orchestrator.ports.sandbox_executor import SandboxExecutor


class JudgeUseCase:
    def __init__(self, sandbox: SandboxExecutor) -> None:
        self._sandbox = sandbox

    def judge(
        self,
        task: MicroTask,
        response: WorkerResponse,
        *,
        retry_count: int = 0,
        llm_secondary_score: float | None = None,
    ) -> Result[JudgeVerdict, str]:
        if response.task_id != task.id:
            return Err("task_id_mismatch")
        contract_ok = response_within_token_budget(response, task.max_tokens)
        sandbox_result = self._sandbox.run_checks(task, response.code)
        if sandbox_result.is_err():
            return Err(sandbox_result.error)  # type: ignore[union-attr]
        checks = sandbox_result.value  # type: ignore[union-attr]
        verdict = score_verdict(
            task_id=task.id,
            sandbox_checks=checks,
            contract_ok=contract_ok,
            llm_secondary_score=llm_secondary_score,
            retry_count=retry_count,
        )
        return Ok(verdict)
