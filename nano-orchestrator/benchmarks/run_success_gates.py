#!/usr/bin/env python3
"""Run EG success gates: GATE-001 / GATE-002 / GATE-003 (+ GATE-NEG if needed).

Compares Orchestration (routed workers + Judge) vs solo Qwen2.5-Coder-0.5B
on the full gold_set.json MicroTasks (fixed tasks — same prompts).

Usage:
  python benchmarks/run_success_gates.py
  python benchmarks/run_success_gates.py --limit 6   # smoke
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.codegen_prompts import (  # noqa: E402
    build_worker_prompt,
    extract_code,
)
from nano_orchestrator.application.judge_use_case import JudgeUseCase  # noqa: E402
from nano_orchestrator.application.pipeline import (  # noqa: E402
    OrchestrationPipeline,
    PipelineConfig,
)
from nano_orchestrator.application.success_gates import (  # noqa: E402
    DEFAULT_P50_TARGET_MS,
    DEFAULT_VRAM_LIMIT_MB,
    gate_001_orchestration_beats_solo,
    gate_002_vram_within_limit,
    gate_003_p50_within_target,
    overall_gates_pass,
)
from nano_orchestrator.domain.entities import MicroTask, WorkerResponse  # noqa: E402
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter  # noqa: E402
from nano_orchestrator.infrastructure.sandbox import CompositeSandbox  # noqa: E402

GOLD = ROOT / "tests" / "golden" / "gold_set.json"
RESULTS = ROOT / "benchmarks" / "RESULTS.md"
OUT_JSON = ROOT / "benchmarks" / "runs" / "success_gates.json"
NEGATIVE = ROOT / "docs" / "NEGATIVE-RESULT.md"
SOLO_MODEL = "qwen25-coder-0.5b"
P50_TARGET_MS = DEFAULT_P50_TARGET_MS


def _load_gold_tasks(limit: int | None) -> list[MicroTask]:
    raw = json.loads(GOLD.read_text(encoding="utf-8"))["tasks"]
    tasks: list[MicroTask] = []
    for item in raw:
        payload = {k: v for k, v in item.items() if k != "gold_code"}
        tasks.append(MicroTask.model_validate(payload))
    if limit is not None:
        tasks = tasks[:limit]
    return tasks


def _vram_mb() -> int | None:
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if proc.returncode != 0:
            return None
        values = [int(x.strip()) for x in proc.stdout.splitlines() if x.strip()]
        return max(values) if values else None
    except (FileNotFoundError, ValueError, subprocess.TimeoutExpired):
        return None


def _restart(model_id: str) -> None:
    stop = ROOT / "scripts" / "stop_model_server.sh"
    start = ROOT / "scripts" / "start_model_server.sh"
    subprocess.run(["bash", str(stop)], cwd=str(ROOT), check=False)
    time.sleep(1)
    proc = subprocess.run(
        ["bash", str(start), model_id],
        cwd=str(ROOT),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"start_failed:{model_id}")


def score_solo(
    tasks: list[MicroTask], *, base_url: str, model_id: str = SOLO_MODEL
) -> dict:
    _restart(model_id)
    adapter = LlamaCppAdapter(base_url, model_id=model_id)
    health = adapter.health()
    if health.is_err():
        raise RuntimeError(health.error)
    judge = JudgeUseCase(CompositeSandbox())
    passed = 0
    latencies: list[int] = []
    by_lang: dict[str, dict[str, int]] = {}
    rows: list[dict] = []
    peak = _vram_mb()
    for task in tasks:
        lang = task.language.value
        by_lang.setdefault(lang, {"passed": 0, "total": 0})
        by_lang[lang]["total"] += 1
        gen = adapter.generate_detailed(
            build_worker_prompt(task), max_tokens=task.max_tokens
        )
        peak = _max(peak, _vram_mb())
        if gen.is_err():
            rows.append({"task_id": task.id, "passed": False, "error": gen.error})
            continue
        result = gen.value  # type: ignore[union-attr]
        latencies.append(result.latency_ms)
        code = extract_code(result.text, task.language)
        response = WorkerResponse(
            task_id=task.id,
            code=code,
            confidence=0.5,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_predicted,
        )
        verdict = judge.judge(task, response)
        ok = verdict.is_ok() and verdict.value.passed  # type: ignore[union-attr]
        if ok:
            passed += 1
            by_lang[lang]["passed"] += 1
        rows.append(
            {
                "task_id": task.id,
                "language": lang,
                "passed": bool(ok),
                "latency_ms": result.latency_ms,
            }
        )
    total = len(tasks) or 1
    return {
        "model_id": model_id,
        "pass_at_1": round(passed / total, 4),
        "passed": passed,
        "total": len(tasks),
        "p50_ms": int(statistics.median(latencies)) if latencies else None,
        "peak_vram_mb": peak,
        "by_lang": {
            lang: {
                "pass_at_1": round(v["passed"] / v["total"], 4) if v["total"] else 0.0,
                **v,
            }
            for lang, v in by_lang.items()
        },
        "rows": rows,
    }


def score_orchestration(
    tasks: list[MicroTask], *, base_url: str, port: int
) -> dict:
    """Fixed gold MicroTasks through pipeline (routing + judge + retries)."""
    subprocess.run(
        ["bash", str(ROOT / "scripts" / "stop_model_server.sh")],
        cwd=str(ROOT),
        check=False,
    )
    time.sleep(1)
    config = PipelineConfig(
        routing=None,  # load config/worker_routing.json
        routing_config_path=ROOT / "config" / "worker_routing.json",
        base_url=base_url,
        port=port,
        out_dir=ROOT / "out" / "gates",
        manage_server=True,
        peak_vram_limit_mb=DEFAULT_VRAM_LIMIT_MB,
    )
    pipeline = OrchestrationPipeline(config)
    started = time.perf_counter()
    result = pipeline.run(
        "GATE-001 gold MicroTask suite (fixed tasks)",
        fixed_tasks=tasks,
    )
    wall_ms = int((time.perf_counter() - started) * 1000)
    if result.is_err():
        raise RuntimeError(result.error)
    payload = result.value  # type: ignore[union-attr]
    passed = sum(1 for v in payload.verdicts.values() if v.passed)
    total = len(tasks) or 1
    latencies = [r.latency_ms for r in payload.responses.values()]
    by_lang: dict[str, dict[str, int]] = {}
    rows: list[dict] = []
    for task in tasks:
        lang = task.language.value
        by_lang.setdefault(lang, {"passed": 0, "total": 0})
        by_lang[lang]["total"] += 1
        verdict = payload.verdicts.get(task.id)
        ok = bool(verdict and verdict.passed)
        if ok:
            by_lang[lang]["passed"] += 1
        resp = payload.responses.get(task.id)
        rows.append(
            {
                "task_id": task.id,
                "language": lang,
                "passed": ok,
                "model_id": payload.routing_used.get(task.id),
                "latency_ms": None if resp is None else resp.latency_ms,
                "score": None if verdict is None else verdict.score,
            }
        )
    return {
        "pass_at_1": round(passed / total, 4),
        "passed": passed,
        "total": len(tasks),
        "p50_ms": int(statistics.median(latencies)) if latencies else None,
        "peak_vram_mb": payload.peak_vram_mb,
        "wall_ms": wall_ms,
        "vram_ok": payload.vram_ok,
        "routing_used": payload.routing_used,
        "by_lang": {
            lang: {
                "pass_at_1": round(v["passed"] / v["total"], 4) if v["total"] else 0.0,
                **v,
            }
            for lang, v in by_lang.items()
        },
        "rows": rows,
    }


def _max(a: int | None, b: int | None) -> int | None:
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def _write_negative_result(payload: dict) -> None:
    solo = payload["solo"]["pass_at_1"]
    orch = payload["orchestration"]["pass_at_1"]
    body = f"""# Negative result — Nano-Orchestrator vs solo 0.5B

**Date:** {payload.get("measured_at", "unknown")}  
**Decision:** **keep solo `Qwen2.5-Coder-0.5B`** — do not stack further orchestration features.

## GATE-001

| Mode | Pass@1 | Passed / Total |
|------|--------|----------------|
| Solo `{SOLO_MODEL}` | {solo:.4f} | {payload["solo"]["passed"]} / {payload["solo"]["total"]} |
| Orchestration (routed workers) | {orch:.4f} | {payload["orchestration"]["passed"]} / {payload["orchestration"]["total"]} |

Orchestration Pass@1 **did not meet or beat** solo baseline on `tests/golden/gold_set.json`.

## Other gates

{json.dumps(payload.get("gates", {}), indent=2)}

## Rationale

Per README §0 success criterion and ADR draft kill criterion: if orchestration loses
to solo 0.5B on the gold set, archive complexity and keep the simpler baseline worker.

Raw numbers: `benchmarks/runs/success_gates.json`
"""
    NEGATIVE.write_text(body, encoding="utf-8")


def _append_results(payload: dict) -> None:
    g1 = payload["gates"]["GATE-001"]
    g2 = payload["gates"]["GATE-002"]
    g3 = payload["gates"]["GATE-003"]
    section = (
        "\n## Success gates (EG)\n\n"
        f"| Gate | Metric | Threshold | Result |\n"
        f"|------|--------|-----------|--------|\n"
        f"| GATE-001 Pass@1 orch ≥ solo | {g1['metric']:.4f} | ≥ {g1['threshold']:.4f} | "
        f"{'PASS' if g1['passed'] else 'FAIL'} |\n"
        f"| GATE-002 peak VRAM ≤ 6000 MB | {g2['metric']:.0f} | ≤ {g2['threshold']:.0f} | "
        f"{'PASS' if g2['passed'] else 'FAIL'} |\n"
        f"| GATE-003 p50 ≤ {P50_TARGET_MS} ms | {g3['metric']:.0f} | ≤ {g3['threshold']:.0f} | "
        f"{'PASS' if g3['passed'] else 'FAIL'} |\n\n"
        f"- Solo overall Pass@1: **{payload['solo']['pass_at_1']:.4f}** "
        f"({payload['solo']['passed']}/{payload['solo']['total']})\n"
        f"- Orch overall Pass@1: **{payload['orchestration']['pass_at_1']:.4f}** "
        f"({payload['orchestration']['passed']}/{payload['orchestration']['total']})\n"
        f"- Orch worker p50: **{payload['orchestration']['p50_ms']} ms**; "
        f"peak VRAM: **{payload['orchestration']['peak_vram_mb']} MB**\n"
    )
    text = RESULTS.read_text(encoding="utf-8") if RESULTS.is_file() else ""
    marker = "## Success gates (EG)"
    if marker in text:
        start = text.index(marker)
        rest = text[start:]
        next_h = rest.find("\n## ", 1)
        text = text[:start] + section.lstrip("\n") + (rest[next_h + 1 :] if next_h != -1 else "")
    else:
        text = text.rstrip() + "\n" + section
    RESULTS.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--p50-target-ms", type=int, default=P50_TARGET_MS)
    parser.add_argument("--skip-solo", action="store_true")
    parser.add_argument("--skip-orch", action="store_true")
    args = parser.parse_args()

    tasks = _load_gold_tasks(args.limit)
    print(f"Gold tasks: {len(tasks)}", file=sys.stderr)

    solo = {
        "model_id": SOLO_MODEL,
        "pass_at_1": 0.0,
        "passed": 0,
        "total": 0,
        "p50_ms": None,
        "peak_vram_mb": None,
        "by_lang": {},
        "rows": [],
    }
    if not args.skip_solo:
        print("Scoring solo baseline…", file=sys.stderr)
        solo = score_solo(tasks, base_url=args.base_url)

    orch = {
        "pass_at_1": 0.0,
        "passed": 0,
        "total": 0,
        "p50_ms": None,
        "peak_vram_mb": None,
        "by_lang": {},
        "rows": [],
    }
    if not args.skip_orch:
        print("Scoring orchestration (fixed gold tasks)…", file=sys.stderr)
        orch = score_orchestration(tasks, base_url=args.base_url, port=args.port)

    v1 = gate_001_orchestration_beats_solo(
        orch_pass_at_1=float(orch["pass_at_1"]),
        solo_pass_at_1=float(solo["pass_at_1"]),
    )
    v2 = gate_002_vram_within_limit(peak_vram_mb=orch.get("peak_vram_mb"))
    v3 = gate_003_p50_within_target(
        p50_ms=orch.get("p50_ms"),
        target_ms=float(args.p50_target_ms),
    )
    gates = {
        v.gate_id: {
            "passed": v.passed,
            "metric": v.metric,
            "threshold": v.threshold,
            "detail": v.detail,
        }
        for v in (v1, v2, v3)
    }
    payload = {
        "measured_at": time.strftime("%Y-%m-%d"),
        "p50_target_ms": args.p50_target_ms,
        "vram_limit_mb": DEFAULT_VRAM_LIMIT_MB,
        "solo": solo,
        "orchestration": orch,
        "gates": gates,
        "all_pass": overall_gates_pass([v1, v2, v3]),
        "gate_neg_required": not v1.passed,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _append_results(payload)
    if not v1.passed:
        _write_negative_result(payload)
        print(f"GATE-NEG written → {NEGATIVE}", file=sys.stderr)
    elif NEGATIVE.is_file():
        # Prior negative obsolete if gate now passes
        NEGATIVE.write_text(
            "# Negative result — superseded\n\n"
            f"GATE-001 now **PASS** ({v1.detail}). See `benchmarks/runs/success_gates.json`.\n",
            encoding="utf-8",
        )

    print(json.dumps(payload, indent=2))
    if not v1.passed:
        return 3
    if not payload["all_pass"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
