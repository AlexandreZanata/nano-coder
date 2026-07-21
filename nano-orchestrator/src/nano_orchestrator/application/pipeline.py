"""End-to-end Orchestrator → Workers → Judge → Merge pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from nano_orchestrator.application.debate import debate_generate, task_requests_debate
from nano_orchestrator.application.dynamic_routing import (
    DebateConfig,
    DynamicRoutingConfig,
    RetryThresholds,
    load_dynamic_routing,
)
from nano_orchestrator.application.judge_use_case import JudgeUseCase
from nano_orchestrator.application.merge_proposal import write_proposal
from nano_orchestrator.application.orchestrate_use_case import OrchestrateUseCase
from nano_orchestrator.application.retry_policy import (
    escalate_to_human,
    retry_budget,
    should_retry,
)
from nano_orchestrator.application.worker_dispatch import (
    WorkerDispatchUseCase,
    WorkerRouting,
    group_tasks_by_model,
)
from nano_orchestrator.domain.entities import JudgeVerdict, MicroTask, WorkerResponse
from nano_orchestrator.domain.result import Err, Ok, Result
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
    routing: WorkerRouting | None = None
    debate: DebateConfig = field(default_factory=DebateConfig)
    retry: RetryThresholds = field(default_factory=RetryThresholds)
    routing_config_path: Path | None = None
    base_url: str = "http://127.0.0.1:8081"
    port: int = 8081
    out_dir: Path = Path("out")
    manage_server: bool = True
    peak_vram_limit_mb: int = 6000

    def resolve_routing(self) -> tuple[WorkerRouting, DebateConfig, RetryThresholds]:
        if self.routing is not None:
            return self.routing, self.debate, self.retry
        dynamic = load_dynamic_routing(self.routing_config_path)
        return dynamic.routing, dynamic.debate, dynamic.retry


@dataclass
class PipelineResult:
    tasks: list[MicroTask]
    responses: dict[str, WorkerResponse]
    verdicts: dict[str, JudgeVerdict]
    escalate: dict[str, bool]
    package_path: Path
    peak_vram_mb: int | None
    vram_ok: bool
    routing_used: dict[str, str] = field(default_factory=dict)


class OrchestrationPipeline:
    def __init__(self, config: PipelineConfig) -> None:
        self._cfg = config

    def run(
        self,
        user_request: str,
        *,
        fixed_tasks: list[MicroTask] | None = None,
    ) -> Result[PipelineResult, str]:
        routing, debate_cfg, retry_cfg = self._cfg.resolve_routing()
        peak = vram_used_mb()
        adapter = LlamaCppAdapter(
            self._cfg.base_url, model_id=self._cfg.orchestrator_model
        )

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

        if self._cfg.manage_server:
            stop_server(self._cfg.port)
            peak = _max_vram(peak)

        judge = JudgeUseCase(CompositeSandbox())
        responses: dict[str, WorkerResponse] = {}
        verdicts: dict[str, JudgeVerdict] = {}
        escalate: dict[str, bool] = {}
        routing_used: dict[str, str] = {}

        grouped = group_tasks_by_model(tasks, routing)
        for model_id, model_tasks in grouped.items():
            if self._cfg.manage_server:
                started = start_server(model_id, port=self._cfg.port)
                if started.is_err():
                    return Err(started.error)  # type: ignore[union-attr]
            adapter = LlamaCppAdapter(self._cfg.base_url, model_id=model_id)
            dispatch = WorkerDispatchUseCase(adapter)
            for task in model_tasks:
                routing_used[task.id] = model_id
                result = self._run_with_retries(
                    dispatch, judge, task, debate_cfg=debate_cfg, retry_cfg=retry_cfg
                )
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
                routing_used=routing_used,
            )
        )

    def _run_with_retries(
        self,
        dispatch: WorkerDispatchUseCase,
        judge: JudgeUseCase,
        task: MicroTask,
        *,
        debate_cfg: DebateConfig,
        retry_cfg: RetryThresholds,
    ) -> Result[tuple[WorkerResponse, JudgeVerdict, bool], str]:
        if task_requests_debate(task, debate_cfg):
            debated = debate_generate(task=task, dispatch=dispatch, judge=judge)
            if debated.is_err():
                return Err(debated.error)  # type: ignore[union-attr]
            response, verdict = debated.value  # type: ignore[union-attr]
            if verdict.passed:
                append_judge_approved(
                    task_id=task.id,
                    language=task.language.value,
                    instruction=task.prompt,
                    code=response.code,
                    score=verdict.score,
                    metadata={"debate": True},
                )
            return Ok((response, verdict, escalate_to_human(verdict, 0, budget=0)))

        last_response: WorkerResponse | None = None
        last_verdict: JudgeVerdict | None = None
        budget = retry_cfg.max_budget
        for attempt in range(retry_cfg.max_budget + 1):
            gen = dispatch.run_task(task)
            if gen.is_err():
                return Err(gen.error)  # type: ignore[union-attr]
            response = gen.value  # type: ignore[union-attr]
            budget = retry_budget(
                response.confidence,
                max_budget=retry_cfg.max_budget,
                high_confidence_min=retry_cfg.high_confidence_min,
                medium_confidence_min=retry_cfg.medium_confidence_min,
            )
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
                    metadata={"retry": attempt, "budget": budget},
                )
                return Ok((response, verdict, False))
            if not should_retry(verdict, attempt, budget=budget):
                break
        assert last_response is not None and last_verdict is not None
        return Ok(
            (
                last_response,
                last_verdict,
                escalate_to_human(last_verdict, attempt, budget=budget),
            )
        )


def _max_vram(current: int | None) -> int | None:
    sample = vram_used_mb()
    if current is None:
        return sample
    if sample is None:
        return current
    return max(current, sample)
