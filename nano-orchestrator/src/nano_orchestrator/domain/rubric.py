"""Pure scoring rubric — sandbox first, LLM last."""

from __future__ import annotations

from nano_orchestrator.domain.entities import JudgeVerdict, WorkerResponse

# Weights MUST sum to 1.0 — change README §3.2 if you change these.
WEIGHT_SANDBOX = 0.60
WEIGHT_CONTRACT = 0.30
WEIGHT_LLM_SECONDARY = 0.10

PASS_THRESHOLD = 0.70
MAX_RETRIES = 2


def score_verdict(
    *,
    task_id: str,
    sandbox_checks: dict[str, bool],
    contract_ok: bool,
    llm_secondary_score: float | None,
    retry_count: int,
) -> JudgeVerdict:
    """Combine checks into a JudgeVerdict without calling any LLM."""
    sandbox_pass = bool(sandbox_checks) and all(sandbox_checks.values())
    sandbox_part = 1.0 if sandbox_pass else 0.0
    contract_part = 1.0 if contract_ok else 0.0
    llm_part = float(llm_secondary_score) if llm_secondary_score is not None else 0.0
    llm_part = max(0.0, min(1.0, llm_part))

    score = (
        WEIGHT_SANDBOX * sandbox_part
        + WEIGHT_CONTRACT * contract_part
        + WEIGHT_LLM_SECONDARY * llm_part
    )
    passed = sandbox_pass and contract_ok and score >= PASS_THRESHOLD
    retry = (not passed) and retry_count < MAX_RETRIES
    return JudgeVerdict(
        task_id=task_id,
        passed=passed,
        score=round(score, 4),
        checks=dict(sandbox_checks),
        retry_recommended=retry,
        feedback=None if passed else "sandbox_or_contract_failed",
    )


def response_within_token_budget(response: WorkerResponse, max_tokens: int) -> bool:
    return response.tokens_used <= max_tokens
