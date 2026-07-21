#!/usr/bin/env python3
"""Phase 2 smoke runner — stub until orchestrator LLM is wired.

Usage:
  python scripts/smoke_runner.py --request "..."
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.judge_use_case import JudgeUseCase
from nano_orchestrator.application.orchestrate_use_case import OrchestrateUseCase
from nano_orchestrator.domain.entities import (
    MicroTask,
    TargetLanguage,
    WorkerResponse,
    WorkerRole,
)
from nano_orchestrator.infrastructure.sandbox import CompositeSandbox


class _StubBackend:
    def generate(self, prompt: str, *, max_tokens: int = 512):
        from nano_orchestrator.domain.result import Err

        return Err("stub_backend")


def _demo_tasks() -> list[MicroTask]:
    """Fixed demo split until Phase 2 LLM decompose is live."""
    return [
        MicroTask(
            id="demo-js",
            role=WorkerRole.CODER,
            language=TargetLanguage.JAVASCRIPT,
            prompt="Export const answer = 42",
            acceptance=["syntax_valid"],
            max_tokens=64,
        ),
        MicroTask(
            id="demo-html",
            role=WorkerRole.CODER,
            language=TargetLanguage.HTML,
            prompt="A single paragraph Hello",
            acceptance=["syntax_valid"],
            max_tokens=64,
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Nano-orchestrator smoke runner")
    parser.add_argument("--request", required=True)
    args = parser.parse_args()

    orch = OrchestrateUseCase(_StubBackend())
    decompose = orch.decompose(args.request)
    if decompose.is_err():
        print(f"NOTE: decompose not wired yet ({decompose.error}) — using demo tasks")
        tasks = _demo_tasks()
    else:
        tasks = decompose.value  # type: ignore[union-attr]

    judge = JudgeUseCase(CompositeSandbox())
    # Demo worker outputs (replace with real worker calls in Phase 2)
    demos = {
        "demo-js": "export const answer = 42;\n",
        "demo-html": "<p>Hello</p>\n",
    }
    results = []
    for task in tasks:
        code = demos.get(task.id, "")
        response = WorkerResponse(
            task_id=task.id,
            code=code,
            confidence=0.5,
            latency_ms=0,
            tokens_used=16,
        )
        verdict = judge.judge(task, response)
        results.append(
            {
                "task": task.model_dump(mode="json"),
                "verdict": verdict.value.model_dump(mode="json")
                if verdict.is_ok()
                else {"error": verdict.error},
            }
        )

    print(json.dumps({"request": args.request, "results": results}, indent=2))
    print("\nHUMAN GATE: review results above — do not auto-persist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
