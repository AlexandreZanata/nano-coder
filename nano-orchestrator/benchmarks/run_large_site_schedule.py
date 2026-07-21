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
    bind_orch_plan_to_slots,
    evaluate_pro_site_quality,
    evaluate_site_quality,
    load_schedule,
    next_slot_same_model,
    should_reuse_server,
    slot_filenames,
    slot_to_task,
)
from nano_orchestrator.application.merge_proposal import (  # noqa: E402
    archive_non_openable,
    write_proposal,
)
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
    server_reused: bool = False
    server_kept_alive: bool = False


def run_orchestrator_slot(
    *,
    model_id: str,
    request: str,
    port: int,
    base_url: str,
    stop_grace_s: float = 1.0,
) -> dict:
    started_at = time.perf_counter()
    peak = vram_used_mb()
    started = start_server(
        model_id, port=port, force_stop=True, stop_grace_s=stop_grace_s
    )
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
    stop_server(port, grace_s=stop_grace_s)
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
    reuse_server: bool = False,
    keep_alive: bool = False,
    settle_s: float = 0.5,
    force_stop: bool = True,
    stop_grace_s: float = 1.0,
) -> tuple[SlotResult, WorkerResponse | None, JudgeVerdict | None]:
    t0 = time.perf_counter()
    peak = vram_used_mb()
    last_error: str | None = None
    best_response: WorkerResponse | None = None
    best_verdict: JudgeVerdict | None = None
    reused = False

    if reuse_server:
        reused = True
    else:
        started = start_server(
            model_id,
            port=port,
            force_stop=force_stop,
            stop_grace_s=stop_grace_s,
        )
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
                    server_reused=False,
                    server_kept_alive=False,
                ),
                None,
                None,
            )
        if settle_s > 0:
            time.sleep(settle_s)

    adapter = LlamaCppAdapter(base_url, model_id=model_id, temperature=0.2)
    dispatch = WorkerDispatchUseCase(adapter)

    def _finish(
        *,
        passed: bool | None,
        score: float | None,
        error: str | None,
        attempts: int,
        quality_ok: bool | None,
        ok: bool,
        latency_ms: int | None,
        tokens_used: int | None,
    ) -> tuple[SlotResult, WorkerResponse | None, JudgeVerdict | None]:
        kept = False
        if keep_alive:
            kept = True
        else:
            stop_server(port, grace_s=stop_grace_s)
        peak_final = _peak(peak, vram_used_mb())
        return (
            SlotResult(
                slot_id=task.id,
                model_id=model_id,
                language=task.language.value,
                ok=ok,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                vram_mb=peak_final,
                passed=passed,
                score=score,
                error=error,
                elapsed_s=time.perf_counter() - t0,
                attempts=attempts,
                quality_ok=quality_ok,
                server_reused=reused,
                server_kept_alive=kept,
            ),
            best_response,
            best_verdict,
        )

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
            return _finish(
                passed=True,
                score=verdict.score,
                error=None,
                attempts=attempt,
                quality_ok=True,
                ok=True,
                latency_ms=response.latency_ms,
                tokens_used=response.tokens_used,
            )
        last_error = "quality_or_judge_failed"

    passed = bool(best_verdict and best_verdict.passed)
    quality = bool(
        best_response and looks_like_code(best_response.code, task.language)
    )
    return _finish(
        passed=passed,
        score=best_verdict.score if best_verdict else None,
        error=None if (passed and quality) else last_error,
        attempts=max_attempts,
        quality_ok=quality,
        ok=best_response is not None,
        latency_ms=best_response.latency_ms if best_response else None,
        tokens_used=best_response.tokens_used if best_response else None,
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
        "--keep-alive",
        action="store_true",
        help="Reuse llama-server across consecutive slots with the same model_id",
    )
    parser.add_argument(
        "--no-keep-alive",
        action="store_true",
        help="Force stop/start every worker slot (disable schedule speed.keep_alive)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Defaults to benchmarks/runs/<schedule-stem>.json",
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
    prefer_orch = bool(schedule.get("prefer_orch_plan", True))
    speed_cfg = dict(schedule.get("speed") or {})
    keep_alive = bool(speed_cfg.get("keep_alive_same_model", False)) or args.keep_alive
    if args.no_keep_alive:
        keep_alive = False
    settle_s = float(speed_cfg.get("settle_s", 0.5))
    stop_grace_s = float(speed_cfg.get("stop_grace_s", 1.0))
    skip_redundant_stop = bool(speed_cfg.get("skip_redundant_stop", False))
    json_out = args.json_out or (
        ROOT / "benchmarks" / "runs" / f"{args.schedule.stem}.json"
    )

    print(f"=== LARGE SITE SCHEDULE start {datetime.now(timezone.utc).isoformat()} ===")
    print(
        f"schedule={args.schedule.name} unique_models={schedule.get('require_unique_models')}"
        f" keep_alive={keep_alive} settle_s={settle_s} stop_grace_s={stop_grace_s}"
    )
    orch_report: dict
    orch_bind_meta: dict = {"bound": 0, "mode": "skipped"}
    if args.skip_orchestrator:
        orch_report = {"ok": None, "skipped": True}
        print("[O0] orchestrator skipped")
    else:
        print(f"[O0] orchestrator {orch_model} decompose (one task → one model)…")
        orch_report = run_orchestrator_slot(
            model_id=orch_model,
            request=request,
            port=args.port,
            base_url=args.base_url,
            stop_grace_s=stop_grace_s,
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
                    "models_monitored": [orch_model],
                }
            )
        )
        if prefer_orch and orch_report.get("ok") and orch_report.get("tasks"):
            slots, orch_bind_meta = bind_orch_plan_to_slots(
                slots, list(orch_report["tasks"])
            )
            print(json.dumps({"orch_bind": orch_bind_meta}))
        else:
            print("[O0] fallback: canonical slots (orch plan unused)")
            orch_bind_meta = {"bound": 0, "mode": "canonical_fallback"}

    judge = JudgeUseCase(CompositeSandbox())
    tasks: list[MicroTask] = []
    responses: dict[str, WorkerResponse] = {}
    verdicts: dict[str, JudgeVerdict] = {}
    escalate: dict[str, bool] = {}
    slot_results: list[SlotResult] = []
    peak_all = vram_used_mb()
    models_used: list[str] = []
    loaded_model: str | None = None
    port_clear_after_orch = (not args.skip_orchestrator) and skip_redundant_stop

    for idx, slot in enumerate(slots, start=1):
        task = slot_to_task(slot)
        model_id = str(slot["model_id"])
        models_used.append(model_id)
        orch_note = slot.get("orch_task_id")
        reuse = should_reuse_server(loaded_model, model_id, keep_alive=keep_alive)
        keep_after = keep_alive and next_slot_same_model(slots, idx - 1)
        force_stop = True
        if (not reuse) and port_clear_after_orch and idx == 1:
            force_stop = False
            port_clear_after_orch = False
        print(
            f"[W{idx}] {task.id} → {model_id} ({task.language.value})"
            + (f" orch={orch_note}" if orch_note else "")
            + (" reuse" if reuse else " cold")
            + (" keep" if keep_after else " stop")
            + (" nostop" if not force_stop and not reuse else "")
            + "…"
        )
        result, response, verdict = run_worker_slot(
            task=task,
            model_id=model_id,
            port=args.port,
            base_url=args.base_url,
            judge=judge,
            max_attempts=max_attempts,
            reuse_server=reuse,
            keep_alive=keep_after,
            settle_s=settle_s,
            force_stop=force_stop,
            stop_grace_s=stop_grace_s,
        )
        if result.server_kept_alive:
            loaded_model = model_id
        else:
            loaded_model = None
        slot_results.append(result)
        print(json.dumps(asdict(result), indent=None))
        if response is not None and verdict is not None:
            tasks.append(task)
            responses[task.id] = response
            verdicts[task.id] = verdict
            escalate[task.id] = not (verdict.passed and bool(result.quality_ok))
        peak_all = _peak(peak_all, result.vram_mb)

    if loaded_model is not None:
        stop_server(args.port, grace_s=stop_grace_s)
        loaded_model = None

    filenames = slot_filenames(slots)
    package_path = None
    archive_report: dict | None = None
    if tasks and len(tasks) == len(responses):
        package_path = write_proposal(
            out_dir=args.out_dir,
            request=request,
            tasks=tasks,
            responses=responses,
            verdicts=verdicts,
            escalate=escalate,
            peak_vram_mb=peak_all,
            filenames=filenames or None,
        )
        if str(schedule.get("kind") or "") == "pro_site":
            archive_report = archive_non_openable(
                out_dir=args.out_dir,
                label="pro-site-non-openable",
            )

    files = {tid: responses[tid].code for tid in responses}
    kind = str(schedule.get("kind") or "bakeoff")
    quality = (
        evaluate_pro_site_quality(files)
        if kind == "pro_site"
        else evaluate_site_quality(files)
    )
    quality_ok = all(quality.values()) if quality else False
    passed_n = sum(1 for s in slot_results if s.passed and s.quality_ok)
    unique_models = sorted(set(models_used))
    # Strict schedules (min_passed == slot_count) also require full quality checklist.
    bar_met = passed_n >= min_passed and (
        quality_ok if min_passed >= len(slot_results) else True
    )
    openable = None
    if package_path and package_path.is_file():
        openable = json.loads(package_path.read_text(encoding="utf-8")).get("openable")
    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "schedule": str(args.schedule),
        "kind": kind,
        "request": request,
        "orchestrator": orch_report,
        "orch_bind": orch_bind_meta,
        "models_monitored": {
            "orchestrator": None if args.skip_orchestrator else orch_model,
            "workers": unique_models,
            "unique_worker_count": len(unique_models),
        },
        "slots": [asdict(s) for s in slot_results],
        "passed_count": passed_n,
        "slot_count": len(slot_results),
        "peak_vram_mb": peak_all,
        "vram_ok": peak_all is None or peak_all <= 6000,
        "package": str(package_path) if package_path else None,
        "openable": openable,
        "archive": archive_report,
        "quality": quality,
        "quality_ok": quality_ok,
        "speed": {
            "keep_alive_same_model": keep_alive,
            "settle_s": settle_s,
            "stop_grace_s": stop_grace_s,
            "skip_redundant_stop": skip_redundant_stop,
            "slots_reused": sum(1 for s in slot_results if s.server_reused),
            "slots_kept_alive": sum(1 for s in slot_results if s.server_kept_alive),
        },
        "pass_bar": {
            "min_passed": min_passed,
            "met": bar_met,
        },
    }

    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": {
        "kind": kind,
        "passed": f"{passed_n}/{len(slot_results)}",
        "quality_ok": quality_ok,
        "quality": quality,
        "openable": openable,
        "archive": archive_report,
        "models_monitored": report["models_monitored"],
        "orch_bind": orch_bind_meta,
        "peak_vram_mb": peak_all,
        "package": report["package"],
        "report": str(json_out),
        "pass_bar_met": report["pass_bar"]["met"],
        "speed": report["speed"],
    }}, indent=2))
    print("\nHUMAN GATE: review out/proposal/ — do not auto-persist.")
    return 0 if report["pass_bar"]["met"] and report["vram_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
