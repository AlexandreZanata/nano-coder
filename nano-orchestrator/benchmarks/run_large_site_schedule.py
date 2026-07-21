#!/usr/bin/env python3
"""Run large-site multi-model schedule — one model per MicroTask.

See benchmarks/LARGE_SITE_TEST_SCHEDULE.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.codegen_prompts import looks_like_code  # noqa: E402
from nano_orchestrator.application.judge_use_case import JudgeUseCase  # noqa: E402
from nano_orchestrator.application.large_site_schedule import (  # noqa: E402
    assert_schedule_valid,
    evaluate_site_quality,
    load_schedule,
    slot_to_task,
)
from nano_orchestrator.application.merge_proposal import write_proposal  # noqa: E402
from nano_orchestrator.application.orchestrate_use_case import OrchestrateUseCase  # noqa: E402
from nano_orchestrator.application.worker_dispatch import WorkerDispatchUseCase  # noqa: E402
from nano_orchestrator.domain.entities import (  # noqa: E402
    JudgeVerdict,
    MicroTask,
    WorkerResponse,
)
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter  # noqa: E402
from nano_orchestrator.infrastructure.model_server import (  # noqa: E402
    start_server,
    stop_server,
    vram_used_mb,
)
from nano_orchestrator.infrastructure.sandbox import CompositeSandbox  # noqa: E402

DEFAULT_SCHEDULE = ROOT / "benchmarks" / "large_site_schedule.json"


def _peak(*vals: int | None) -> int | None:
    nums = [v for v in vals if v is not None]
    return max(nums) if nums else None


@dataclass
class SlotResult:
    slot_id: str
    model_id: str
    language: str
    ok: bool
    latency_ms: int | None
    tokens_used: int | None
    vram_mb: int | None
    passed: bool | None
    score: float | None
    error: str | None
    elapsed_s: float
    attempts: int = 1
    quality_ok: bool | None = None


def run_orchestrator_slot(
    *,
    model_id: str,
    request: str,
    port: int,
    base_url: str,
) -> dict:
    started_at = time.perf_counter()
    peak = vram_used_mb()
    started = start_server(model_id, port=port)
    if started.is_err():
        return {
            "ok": False,
            "error": started.error,
            "elapsed_s": time.perf_counter() - started_at,
            "vram_mb": vram_used_mb(),
            "tasks": None,
            "raw_ok": False,
        }
    adapter = LlamaCppAdapter(base_url, model_id=model_id, temperature=0.1)
    orch = OrchestrateUseCase(adapter, max_tokens=768)
    decomposed = orch.decompose(request)
    peak = _peak(peak, vram_used_mb())
    stop_server(port)
    elapsed = time.perf_counter() - started_at
    if decomposed.is_err():
        return {
            "ok": False,
            "error": decomposed.error,
            "elapsed_s": elapsed,
            "vram_mb": peak,
            "tasks": None,
            "raw_ok": False,
        }
    tasks = decomposed.value  # type: ignore[union-attr]
    return {
        "ok": True,
        "error": None,
        "elapsed_s": elapsed,
        "vram_mb": peak,
        "tasks": [t.model_dump(mode="json") for t in tasks],
        "raw_ok": True,
        "count": len(tasks),
    }


def run_worker_slot(
    *,
    task: MicroTask,
    model_id: str,
    port: int,
    base_url: str,
    judge: JudgeUseCase,
    max_attempts: int = 2,
) -> tuple[SlotResult, WorkerResponse | None, JudgeVerdict | None]:
    t0 = time.perf_counter()
    peak = vram_used_mb()
    last_error: str | None = None
    best_response: WorkerResponse | None = None
    best_verdict: JudgeVerdict | None = None

    started = start_server(model_id, port=port)
    if started.is_err():
        return (
            SlotResult(
                slot_id=task.id,
                model_id=model_id,
                language=task.language.value,
                ok=False,
                latency_ms=None,
                tokens_used=None,
                vram_mb=vram_used_mb(),
                passed=None,
                score=None,
                error=str(started.error),
                elapsed_s=time.perf_counter() - t0,
                attempts=0,
                quality_ok=False,
            ),
            None,
            None,
        )

    adapter = LlamaCppAdapter(base_url, model_id=model_id, temperature=0.1)
    dispatch = WorkerDispatchUseCase(adapter)

    for attempt in range(1, max_attempts + 1):
        gen = dispatch.run_task(task)
        peak = _peak(peak, vram_used_mb())
        if gen.is_err():
            last_error = str(gen.error)
            continue
        response = gen.value  # type: ignore[union-attr]
        judged = judge.judge(task, response)
        if judged.is_err():
            last_error = str(judged.error)
            continue
        verdict = judged.value  # type: ignore[union-attr]
        quality = looks_like_code(response.code, task.language)
        best_response = response
        best_verdict = verdict
        if verdict.passed and quality:
            stop_server(port)
            peak = _peak(peak, vram_used_mb())
            return (
                SlotResult(
                    slot_id=task.id,
                    model_id=model_id,
                    language=task.language.value,
                    ok=True,
                    latency_ms=response.latency_ms,
                    tokens_used=response.tokens_used,
                    vram_mb=peak,
                    passed=True,
                    score=verdict.score,
                    error=None,
                    elapsed_s=time.perf_counter() - t0,
                    attempts=attempt,
                    quality_ok=True,
                ),
                response,
                verdict,
            )
        last_error = "quality_or_judge_failed"

    stop_server(port)
    peak = _peak(peak, vram_used_mb())
    passed = bool(best_verdict and best_verdict.passed)
    quality = bool(
        best_response and looks_like_code(best_response.code, task.language)
    )
    return (
        SlotResult(
            slot_id=task.id,
            model_id=model_id,
            language=task.language.value,
            ok=best_response is not None,
            latency_ms=best_response.latency_ms if best_response else None,
            tokens_used=best_response.tokens_used if best_response else None,
            vram_mb=peak,
            passed=passed,
            score=best_verdict.score if best_verdict else None,
            error=None if (passed and quality) else last_error,
            elapsed_s=time.perf_counter() - t0,
            attempts=max_attempts,
            quality_ok=quality,
        ),
        best_response,
        best_verdict,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Large-site multi-model schedule")
    parser.add_argument("--schedule", type=Path, default=DEFAULT_SCHEDULE)
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "out")
    parser.add_argument(
        "--skip-orchestrator",
        action="store_true",
        help="Skip live decompose; run canonical slots only",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=ROOT / "benchmarks" / "runs" / "large_site_schedule.json",
    )
    args = parser.parse_args()

    schedule = load_schedule(args.schedule)
    try:
        assert_schedule_valid(schedule)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    request = str(schedule["request"])
    orch_model = str(schedule.get("orchestrator_model") or "smollm3-3b")
    slots = list(schedule["slots"])
    min_passed = int(schedule.get("min_passed") or len(slots))
    max_attempts = int(schedule.get("max_retries_per_slot") or 2)

    print(f"=== LARGE SITE SCHEDULE start {datetime.now(timezone.utc).isoformat()} ===")
    orch_report: dict
    if args.skip_orchestrator:
        orch_report = {"ok": None, "skipped": True}
        print("[O0] orchestrator skipped")
    else:
        print(f"[O0] orchestrator {orch_model} decompose…")
        orch_report = run_orchestrator_slot(
            model_id=orch_model,
            request=request,
            port=args.port,
            base_url=args.base_url,
        )
        print(
            json.dumps(
                {
                    "slot": "O0",
                    "ok": orch_report.get("ok"),
                    "error": orch_report.get("error"),
                    "count": orch_report.get("count"),
                    "vram_mb": orch_report.get("vram_mb"),
                    "elapsed_s": round(float(orch_report.get("elapsed_s") or 0), 2),
                }
            )
        )

    judge = JudgeUseCase(CompositeSandbox())
    tasks: list[MicroTask] = []
    responses: dict[str, WorkerResponse] = {}
    verdicts: dict[str, JudgeVerdict] = {}
    escalate: dict[str, bool] = {}
    slot_results: list[SlotResult] = []
    peak_all = vram_used_mb()

    for idx, slot in enumerate(slots, start=1):
        task = slot_to_task(slot)
        model_id = str(slot["model_id"])
        print(f"[W{idx}] {task.id} → {model_id} ({task.language.value})…")
        result, response, verdict = run_worker_slot(
            task=task,
            model_id=model_id,
            port=args.port,
            base_url=args.base_url,
            judge=judge,
            max_attempts=max_attempts,
        )
        slot_results.append(result)
        print(json.dumps(asdict(result), indent=None))
        if response is not None and verdict is not None:
            tasks.append(task)
            responses[task.id] = response
            verdicts[task.id] = verdict
            escalate[task.id] = not (verdict.passed and bool(result.quality_ok))
        peak_all = _peak(peak_all, result.vram_mb)

    package_path = None
    if tasks and len(tasks) == len(responses):
        package_path = write_proposal(
            out_dir=args.out_dir,
            request=request,
            tasks=tasks,
            responses=responses,
            verdicts=verdicts,
            escalate=escalate,
            peak_vram_mb=peak_all,
        )

    files = {
        tid: responses[tid].code
        for tid in responses
    }
    quality = evaluate_site_quality(files)
    quality_ok = all(quality.values()) if quality else False
    passed_n = sum(1 for s in slot_results if s.passed and s.quality_ok)
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "schedule": str(args.schedule),
        "request": request,
        "orchestrator": orch_report,
        "slots": [asdict(s) for s in slot_results],
        "passed_count": passed_n,
        "slot_count": len(slot_results),
        "peak_vram_mb": peak_all,
        "vram_ok": peak_all is None or peak_all <= 6000,
        "package": str(package_path) if package_path else None,
        "quality": quality,
        "quality_ok": quality_ok,
        "pass_bar": {
            "min_passed": min_passed,
            "met": passed_n >= min_passed and quality_ok,
        },
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": {
        "passed": f"{passed_n}/{len(slot_results)}",
        "quality_ok": quality_ok,
        "quality": quality,
        "peak_vram_mb": peak_all,
        "package": report["package"],
        "report": str(args.json_out),
        "pass_bar_met": report["pass_bar"]["met"],
    }}, indent=2))
    print("\nHUMAN GATE: review out/proposal/ — do not auto-persist.")
    return 0 if report["pass_bar"]["met"] and report["vram_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
