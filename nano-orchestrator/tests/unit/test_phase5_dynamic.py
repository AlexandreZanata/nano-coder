"""Phase 5 — dynamic routing, adaptive retry, optional debate."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.application.debate import (
    DEBATE_COST_MULTIPLIER,
    debate_generate,
    task_requests_debate,
)
from nano_orchestrator.application.dynamic_routing import (
    DebateConfig,
    build_routing_from_scores,
    load_dynamic_routing,
    select_best_model,
)
from nano_orchestrator.application.retry_policy import (
    escalate_to_human,
    retry_budget,
    should_retry,
)
from nano_orchestrator.application.worker_dispatch import estimate_confidence
from nano_orchestrator.domain.entities import (
    JudgeVerdict,
    MicroTask,
    TargetLanguage,
    WorkerResponse,
    WorkerRole,
)
from nano_orchestrator.domain.result import Ok

ROOT = Path(__file__).resolve().parents[2]
ROUTING_CONFIG = ROOT / "config" / "worker_routing.json"


def test_select_best_model_prefers_higher_pass() -> None:
    model = select_best_model(
        [
            {"model_id": "a", "pass_at_1": 0.5, "p50_ms": 100},
            {"model_id": "b", "pass_at_1": 0.9, "p50_ms": 400},
        ],
        fallback="fallback",
    )
    assert model == "b"


def test_select_best_model_tie_break_lower_p50() -> None:
    model = select_best_model(
        [
            {"model_id": "slow", "pass_at_1": 0.8, "p50_ms": 500},
            {"model_id": "fast", "pass_at_1": 0.8, "p50_ms": 200},
        ],
        fallback="fallback",
    )
    assert model == "fast"


def test_load_dynamic_routing_prefers_fine_tuned() -> None:
    cfg = load_dynamic_routing(ROUTING_CONFIG)
    assert cfg.debate.enabled is False
    assert cfg.prefer_fine_tuned is True
    assert cfg.routing.javascript.endswith("-javascript-ft")
    assert cfg.routing.html.endswith("-html-ft")
    assert cfg.routing.freemarker.endswith("-freemarker-ft")


def test_build_routing_without_ft_uses_bakeoff_winner() -> None:
    scores = {
        "javascript": [
            {"model_id": "qwen25-coder-0.5b", "pass_at_1": 0.9, "p50_ms": 357},
            {"model_id": "smollm2-360m", "pass_at_1": 0.8, "p50_ms": 299},
        ],
        "html": [
            {"model_id": "qwen25-coder-0.5b", "pass_at_1": 0.9, "p50_ms": 357},
        ],
        "freemarker": [
            {"model_id": "smollm2-360m", "pass_at_1": 0.0, "p50_ms": 299},
            {"model_id": "qwen25-coder-0.5b", "pass_at_1": 0.0, "p50_ms": 357},
        ],
    }
    routing = build_routing_from_scores(
        scores, fallback="qwen25-coder-0.5b", prefer_fine_tuned=False
    )
    assert routing.javascript == "qwen25-coder-0.5b"
    assert routing.html == "qwen25-coder-0.5b"
    # tie on pass → lower p50 wins
    assert routing.freemarker == "smollm2-360m"


def test_retry_budget_by_confidence() -> None:
    assert retry_budget(0.95) == 0
    assert retry_budget(0.6) == 1
    assert retry_budget(0.2) == 2
    assert retry_budget(0.2, max_budget=1) == 1


def test_should_retry_respects_adaptive_budget() -> None:
    verdict = JudgeVerdict(
        task_id="t",
        passed=False,
        score=0.1,
        checks={"syntax": False},
        retry_recommended=True,
    )
    assert should_retry(verdict, 0, budget=0) is False
    assert should_retry(verdict, 0, budget=2) is True
    assert should_retry(verdict, 1, budget=1) is False
    assert escalate_to_human(verdict, 0, budget=0) is True


def test_estimate_confidence_rewards_fenced_code() -> None:
    low = estimate_confidence("sure", "x")
    high = estimate_confidence("```js\nexport const x = 1;\n```", "export const x = 1;\n")
    assert high > low


def test_debate_default_off_even_with_critical() -> None:
    task = MicroTask(
        id="c1",
        role=WorkerRole.CODER,
        language=TargetLanguage.JAVASCRIPT,
        prompt="critical helper",
        acceptance=["syntax_valid", "critical"],
    )
    assert task_requests_debate(task, DebateConfig(enabled=False)) is False
    assert task_requests_debate(task, DebateConfig(enabled=True)) is True


def test_debate_picks_higher_score() -> None:
    task = MicroTask(
        id="c1",
        role=WorkerRole.CODER,
        language=TargetLanguage.JAVASCRIPT,
        prompt="export const x = 1",
        acceptance=["syntax_valid", "critical"],
        max_tokens=64,
    )

    class _Disp:
        def __init__(self) -> None:
            self.n = 0

        def run_task(self, _task: MicroTask):
            self.n += 1
            code = "function (\n" if self.n == 1 else "export const x = 1;\n"
            return Ok(
                WorkerResponse(
                    task_id="c1",
                    code=code,
                    confidence=0.5,
                    latency_ms=1,
                    tokens_used=3,
                )
            )

    class _Judge:
        def judge(self, task: MicroTask, response: WorkerResponse, *, retry_count: int = 0):
            from nano_orchestrator.application.judge_use_case import JudgeUseCase
            from nano_orchestrator.infrastructure.sandbox import CompositeSandbox

            return JudgeUseCase(CompositeSandbox()).judge(
                task, response, retry_count=retry_count
            )

    result = debate_generate(task=task, dispatch=_Disp(), judge=_Judge(), rounds=2)
    assert result.is_ok()
    response, verdict = result.value  # type: ignore[misc]
    assert "x = 1" in response.code
    assert verdict.passed is True


def test_debate_cost_multiplier_documented() -> None:
    assert DEBATE_COST_MULTIPLIER == 2.5


def test_routing_config_json_debate_off() -> None:
    payload = json.loads(ROUTING_CONFIG.read_text(encoding="utf-8"))
    assert payload["debate"]["enabled"] is False
    assert "2.5" in payload["debate"]["cost_multiplier_note"]
