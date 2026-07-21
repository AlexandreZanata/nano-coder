"""Optional debate path for critical MicroTasks (Phase 5) — default OFF."""

from __future__ import annotations

from nano_orchestrator.application.dynamic_routing import DebateConfig
from nano_orchestrator.application.judge_use_case import JudgeUseCase
from nano_orchestrator.application.worker_dispatch import WorkerDispatchUseCase
from nano_orchestrator.domain.entities import JudgeVerdict, MicroTask, WorkerResponse
from nano_orchestrator.domain.result import Err, Ok, Result

# Documented cost multiplier when debate runs (two generations + dual judge).
DEBATE_COST_MULTIPLIER = 2.5


def task_requests_debate(task: MicroTask, config: DebateConfig) -> bool:
    if not config.enabled:
        return False
    token = config.acceptance_token.strip().lower()
    return any(str(item).strip().lower() == token for item in task.acceptance)


def debate_generate(
    *,
    task: MicroTask,
    dispatch: WorkerDispatchUseCase,
    judge: JudgeUseCase,
    rounds: int = 2,
) -> Result[tuple[WorkerResponse, JudgeVerdict], str]:
    """Generate up to `rounds` candidates; keep highest Judge score (sandbox-first)."""
    if rounds < 2:
        return Err("debate_rounds_lt_2")
    best_response: WorkerResponse | None = None
    best_verdict: JudgeVerdict | None = None
    for _ in range(rounds):
        gen = dispatch.run_task(task)
        if gen.is_err():
            continue
        response = gen.value  # type: ignore[union-attr]
        judged = judge.judge(task, response, retry_count=0)
        if judged.is_err():
            continue
        verdict = judged.value  # type: ignore[union-attr]
        if best_verdict is None or verdict.score > best_verdict.score:
            best_response, best_verdict = response, verdict
            if verdict.passed:
                break
    if best_response is None or best_verdict is None:
        return Err("debate_no_candidate")
    return Ok((best_response, best_verdict))
