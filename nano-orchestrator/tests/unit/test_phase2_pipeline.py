"""Unit tests for Phase 2 decompose / dispatch / merge / retry."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.application.merge_proposal import sort_tasks, write_proposal
from nano_orchestrator.application.orchestrate_use_case import OrchestrateUseCase
from nano_orchestrator.application.retry_policy import escalate_to_human, should_retry
from nano_orchestrator.application.worker_dispatch import WorkerRouting, group_tasks_by_model
from nano_orchestrator.domain.entities import (
    JudgeVerdict,
    MicroTask,
    TargetLanguage,
    WorkerResponse,
    WorkerRole,
)
from nano_orchestrator.domain.microtask_parser import parse_microtasks_json
from nano_orchestrator.domain.result import Ok
from nano_orchestrator.domain.rubric import MAX_RETRIES


class _FakeBackend:
    def __init__(self, text: str) -> None:
        self._text = text

    def generate(self, prompt: str, *, max_tokens: int = 512):
        return Ok(self._text)


def _task(tid: str, lang: TargetLanguage) -> MicroTask:
    return MicroTask(
        id=tid,
        role=WorkerRole.CODER,
        language=lang,
        prompt="x",
        acceptance=["syntax_valid"],
        max_tokens=64,
    )


def test_parse_rejects_invalid_json() -> None:
    result = parse_microtasks_json("not json")
    assert result.is_err()
    assert "invalid_json" in result.error  # type: ignore[union-attr]


def test_parse_rejects_more_than_five_tasks() -> None:
    items = [
        {
            "id": f"t{i}",
            "role": "coder",
            "language": "javascript",
            "prompt": "p",
            "acceptance": ["syntax_valid"],
            "max_tokens": 32,
        }
        for i in range(6)
    ]
    result = parse_microtasks_json(json.dumps(items))
    assert result.is_err()
    assert "worker_cap" in result.error  # type: ignore[union-attr]


def test_parse_accepts_array_with_trailing_garbage() -> None:
    raw = (
        '[{"id":"a","role":"coder","language":"javascript",'
        '"prompt":"clamp","constraints":[],"acceptance":["syntax_valid"],'
        '"max_tokens":64}]\nHere is more text'
    )
    result = parse_microtasks_json(raw)
    assert result.is_ok()


def test_orchestrate_decompose_wires_parser() -> None:
    raw = (
        '[{"id":"a","role":"coder","language":"javascript",'
        '"prompt":"clamp","constraints":[],"acceptance":["syntax_valid"],'
        '"max_tokens":64}]'
    )
    use_case = OrchestrateUseCase(_FakeBackend(raw))
    result = use_case.decompose("make clamp")
    assert result.is_ok()
    assert len(result.value) == 1  # type: ignore[union-attr]


def test_worker_routing_groups_by_model() -> None:
    tasks = [
        _task("js", TargetLanguage.JAVASCRIPT),
        _task("html", TargetLanguage.HTML),
        _task("ftl", TargetLanguage.FREEMARKER),
    ]
    grouped = group_tasks_by_model(tasks, WorkerRouting())
    assert "qwen25-coder-0.5b" in grouped
    assert "smollm2-360m" in grouped
    assert len(grouped["smollm2-360m"]) == 1


def test_retry_then_escalate() -> None:
    verdict = JudgeVerdict(
        task_id="t",
        passed=False,
        score=0.1,
        checks={"syntax": False},
        retry_recommended=True,
    )
    assert should_retry(verdict, 0) is True
    assert should_retry(verdict, MAX_RETRIES) is False
    assert escalate_to_human(verdict, MAX_RETRIES) is True


def test_merge_writes_only_under_proposal(tmp_path: Path) -> None:
    task = _task("smoke-js", TargetLanguage.JAVASCRIPT)
    response = WorkerResponse(
        task_id="smoke-js",
        code="export const x = 1;\n",
        confidence=0.5,
        latency_ms=1,
        tokens_used=3,
    )
    verdict = JudgeVerdict(
        task_id="smoke-js",
        passed=True,
        score=0.9,
        checks={"syntax": True},
        retry_recommended=False,
    )
    path = write_proposal(
        out_dir=tmp_path,
        request="req",
        tasks=[task],
        responses={"smoke-js": response},
        verdicts={"smoke-js": verdict},
        escalate={"smoke-js": False},
        peak_vram_mb=1000,
    )
    assert path.name == "package.json"
    assert (tmp_path / "proposal" / "smoke-js.js").is_file()
    assert path.is_relative_to(tmp_path / "proposal")


def test_sort_tasks_language_then_id() -> None:
    tasks = [
        _task("b", TargetLanguage.HTML),
        _task("a", TargetLanguage.JAVASCRIPT),
        _task("c", TargetLanguage.FREEMARKER),
    ]
    ordered = sort_tasks(tasks)
    assert [t.id for t in ordered] == ["a", "b", "c"]
