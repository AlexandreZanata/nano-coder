"""Security / ASI08 assertions for nano-orchestrator (T-074)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.application.merge_proposal import sort_tasks, write_proposal
from nano_orchestrator.domain.entities import (
    JudgeVerdict,
    MicroTask,
    TargetLanguage,
    WorkerResponse,
    WorkerRole,
)
from nano_orchestrator.domain.rubric import MAX_RETRIES
from nano_orchestrator.domain.task_splitter import MAX_ACTIVE_WORKERS, assert_worker_cap
from nano_orchestrator.infrastructure.llm_call_log import append_llm_call, prompt_hash

ROOT = Path(__file__).resolve().parents[2]


def test_asi08_worker_cap_is_five() -> None:
    assert MAX_ACTIVE_WORKERS == 5


def test_asi08_retry_cap_is_two() -> None:
    assert MAX_RETRIES == 2


def test_asi08_six_tasks_rejected() -> None:
    tasks = [
        MicroTask(
            id=f"t{i}",
            role=WorkerRole.CODER,
            language=TargetLanguage.JAVASCRIPT,
            prompt="p",
            acceptance=["syntax_valid"],
        )
        for i in range(6)
    ]
    try:
        assert_worker_cap(tasks)
        raise AssertionError("expected worker cap error")
    except ValueError as exc:
        assert "ASI08" in str(exc) or "worker cap" in str(exc)


def test_human_gate_auto_persist_false(tmp_path: Path) -> None:
    task = MicroTask(
        id="sec-js",
        role=WorkerRole.CODER,
        language=TargetLanguage.JAVASCRIPT,
        prompt="x",
        acceptance=["syntax_valid"],
    )
    response = WorkerResponse(
        task_id="sec-js",
        code="export const x = 1;\n",
        confidence=0.5,
        latency_ms=1,
        tokens_used=2,
    )
    verdict = JudgeVerdict(
        task_id="sec-js",
        passed=True,
        score=0.9,
        checks={"syntax": True},
        retry_recommended=False,
    )
    path = write_proposal(
        out_dir=tmp_path,
        request="req",
        tasks=[task],
        responses={"sec-js": response},
        verdicts={"sec-js": verdict},
        escalate={"sec-js": False},
        peak_vram_mb=100,
    )
    package = json.loads(path.read_text(encoding="utf-8"))
    assert package["auto_persist"] is False
    assert package["human_gate"] is True
    assert path.is_relative_to(tmp_path / "proposal")
    # Must not escape proposal dir
    assert "proposal" in path.parts


def test_llm_call_log_redacts_raw_prompt(tmp_path: Path) -> None:
    secret = "Bearer SUPER_SECRET_TOKEN_do_not_log"
    log_path = tmp_path / "llm_calls.jsonl"
    append_llm_call(
        model_id="qwen25-coder-0.5b",
        prompt=secret,
        latency_ms=10,
        ok=True,
        log_path=log_path,
    )
    raw = log_path.read_text(encoding="utf-8")
    assert "SUPER_SECRET" not in raw
    assert "Bearer" not in raw
    row = json.loads(raw.strip())
    assert row["prompt_hash"] == prompt_hash(secret)
    assert "prompt" not in row
    assert "code" not in row


def test_sort_tasks_deterministic_order() -> None:
    tasks = [
        MicroTask(
            id="b",
            role=WorkerRole.CODER,
            language=TargetLanguage.HTML,
            prompt="p",
            acceptance=["syntax_valid"],
        ),
        MicroTask(
            id="a",
            role=WorkerRole.CODER,
            language=TargetLanguage.JAVASCRIPT,
            prompt="p",
            acceptance=["syntax_valid"],
        ),
    ]
    ordered = sort_tasks(tasks)
    assert [t.id for t in ordered] == ["a", "b"]


def test_negative_result_doc_exists() -> None:
    path = ROOT / "docs" / "NEGATIVE-RESULT.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "keep solo" in text.lower()
    assert "GATE-001" in text
