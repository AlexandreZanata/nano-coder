"""End-to-end Orchestrator → Workers → Judge → Merge pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from nano_orchestrator.application.judge_use_case import JudgeUseCase
from nano_orchestrator.application.merge_proposal import write_proposal
from nano_orchestrator.application.orchestrate_use_case import OrchestrateUseCase
from nano_orchestrator.application.retry_policy import escalate_to_human, should_retry
from nano_orchestrator.application.worker_dispatch import (
    WorkerDispatchUseCase,
    WorkerRouting,
    group_tasks_by_model,
)
from nano_orchestrator.domain.entities import JudgeVerdict, MicroTask, WorkerResponse
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.domain.rubric import MAX_RETRIES
from nano_orchestrator.infrastructure.judge_approved_log import append_judge_approved
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter
from nano_orchestrator.infrastructure.model_server import (
    start_server,
    stop_server,
    vram_used_mb,
)
from nano_orchestrator.infrastructure.sandbox import CompositeSandbox


@dataclass
class PipelineConfig:
    orchestrator_model: str = "smollm3-3b"
    routing: WorkerRouting = field(default_factory=WorkerRouting)
    base_url: str = "http://127.0.0.1:8081"
    port: int = 8081
    out_dir: Path = Path("out")
    manage_server: bool = True
    peak_vram_limit_mb: int = 6000


@dataclass
class PipelineResult:
    tasks: list[MicroTask]
    responses: dict[str, WorkerResponse]
    verdicts: dict[str, JudgeVerdict]
    escalate: dict[str, bool]
    package_path: Path
    peak_vram_mb: int | None
    vram_ok: bool


class OrchestrationPipeline:
    def __init__(self, config: PipelineConfig) -> None:
        self._cfg = config

    def run(
        self,
        user_request: str,
        *,
        fixed_tasks: list[MicroTask] | None = None,
    ) -> Result[PipelineResult, str]:
        peak = vram_used_mb()
        adapter = LlamaCppAdapter(
            self._cfg.base_url, model_id=self._cfg.orchestrator_model
        )

        # --- Decompose (orchestrator resident) ---
        if fixed_tasks is not None:
            tasks = fixed_tasks
        else:
            if self._cfg.manage_server:
                started = start_server(self._cfg.orchestrator_model, port=self._cfg.port)
                if started.is_err():
                    return Err(started.error)  # type: ignore[union-attr]
            health = adapter.health()
            if health.is_err():
                return Err(health.error)  # type: ignore[union-attr]
            orch = OrchestrateUseCase(adapter)
            decomposed = orch.decompose(user_request)
            if decomposed.is_err():
                return Err(decomposed.error)  # type: ignore[union-attr]
            tasks = decomposed.value  # type: ignore[union-attr]

        peak = _max_vram(peak)

        # --- VRAM policy: unload orchestrator before workers ---
        if self._cfg.manage_server:
            stop_server(self._cfg.port)
            peak = _max_vram(peak)

        judge = JudgeUseCase(CompositeSandbox())
        responses: dict[str, WorkerResponse] = {}
        verdicts: dict[str, JudgeVerdict] = {}
        escalate: dict[str, bool] = {}

        grouped = group_tasks_by_model(tasks, self._cfg.routing)
        for model_id, model_tasks in grouped.items():
            if self._cfg.manage_server:
                started = start_server(model_id, port=self._cfg.port)
                if started.is_err():
                    return Err(started.error)  # type: ignore[union-attr]
            adapter = LlamaCppAdapter(self._cfg.base_url, model_id=model_id)
            dispatch = WorkerDispatchUseCase(adapter)
            for task in model_tasks:
                result = self._run_with_retries(dispatch, judge, task)
                if result.is_err():
                    return Err(result.error)  # type: ignore[union-attr]
                response, verdict, escalated = result.value  # type: ignore[union-attr]
                responses[task.id] = response
                verdicts[task.id] = verdict
                escalate[task.id] = escalated
                peak = _max_vram(peak)

        if self._cfg.manage_server:
            stop_server(self._cfg.port)
            peak = _max_vram(peak)

        package_path = write_proposal(
            out_dir=self._cfg.out_dir,
            request=user_request,
            tasks=tasks,
            responses=responses,
            verdicts=verdicts,
            escalate=escalate,
            peak_vram_mb=peak,
        )
        vram_ok = peak is None or peak <= self._cfg.peak_vram_limit_mb
        return Ok(
            PipelineResult(
                tasks=tasks,
                responses=responses,
                verdicts=verdicts,
                escalate=escalate,
                package_path=package_path,
                peak_vram_mb=peak,
                vram_ok=vram_ok,
            )
        )

    def _run_with_retries(
        self,
        dispatch: WorkerDispatchUseCase,
        judge: JudgeUseCase,
        task: MicroTask,
    ) -> Result[tuple[WorkerResponse, JudgeVerdict, bool], str]:
        last_response: WorkerResponse | None = None
        last_verdict: JudgeVerdict | None = None
        for attempt in range(MAX_RETRIES + 1):
            gen = dispatch.run_task(task)
            if gen.is_err():
                return Err(gen.error)  # type: ignore[union-attr]
            response = gen.value  # type: ignore[union-attr]
            judged = judge.judge(task, response, retry_count=attempt)
            if judged.is_err():
                return Err(judged.error)  # type: ignore[union-attr]
            verdict = judged.value  # type: ignore[union-attr]
            last_response, last_verdict = response, verdict
            if verdict.passed:
                append_judge_approved(
                    task_id=task.id,
                    language=task.language.value,
                    instruction=task.prompt,
                    code=response.code,
                    score=verdict.score,
                    metadata={"retry": attempt},
                )
                return Ok((response, verdict, False))
            if not should_retry(verdict, attempt):
                break
        assert last_response is not None and last_verdict is not None
        return Ok(
            (
                last_response,
                last_verdict,
                escalate_to_human(last_verdict, MAX_RETRIES),
            )
        )


def _max_vram(current: int | None) -> int | None:
    sample = vram_used_mb()
    if current is None:
        return sample
    if sample is None:
        return current
    return max(current, sample)
