"""Unit tests for smoke evaluation (Stage 8)."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.smoke_eval import (
    evaluate_smoke_task,
    load_held_out_tasks,
    summarize_smoke_eval,
)
from nano_coder.domain.target_language import TargetLanguage

ROOT = Path(__file__).resolve().parents[2]


def test_evaluate_smoke_task_accepts_valid_javascript():
    task = {
        "id": "ho-js-001",
        "acceptanceCriteria": {
            "mustParse": True,
            "mustContain": ["jwt", "refresh token"],
            "mustNotContain": ["TODO"],
        },
    }
    code = (
        "/** jwt refresh token */\n"
        "export function authMiddleware() {\n  return 'jwt refresh token';\n}\n"
    )
    result = evaluate_smoke_task(task, code, language=TargetLanguage.JAVASCRIPT)
    assert result.passed


def test_evaluate_smoke_task_rejects_missing_keyword():
    task = {
        "id": "ho-js-001",
        "acceptanceCriteria": {"mustContain": ["jwt"], "mustNotContain": ["TODO"]},
    }
    code = "export function authMiddleware() { return 'token'; }\n"
    result = evaluate_smoke_task(task, code, language=TargetLanguage.JAVASCRIPT)
    assert not result.passed
    assert result.reason is not None


def test_load_held_out_tasks_returns_limited_subset():
    tasks = load_held_out_tasks(
        ROOT / "data" / "benchmarks" / "held-out-v1",
        TargetLanguage.JAVASCRIPT,
        limit=5,
    )
    assert len(tasks) == 5


def test_summarize_smoke_eval_gate():
    from nano_coder.domain.smoke_eval import SmokeTaskResult

    summary = summarize_smoke_eval(
        [SmokeTaskResult("a", True, None), SmokeTaskResult("b", False, "x")],
        min_pass_at_1=0.60,
    )
    assert summary.pass_at_1 == 0.5
    assert not summary.gate_satisfied
