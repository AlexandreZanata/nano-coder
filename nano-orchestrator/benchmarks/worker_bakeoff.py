#!/usr/bin/env python3
"""Worker / orchestrator bake-off against frozen gold set.

Examples:
  python benchmarks/worker_bakeoff.py --mode worker --model-id qwen25-coder-0.5b \\
      --base-url http://127.0.0.1:8081 --write-results

  python benchmarks/worker_bakeoff.py --mode orchestrator --model-id smollm3-3b \\
      --base-url http://127.0.0.1:8081 --write-results
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.bakeoff_metrics import BakeoffSummary, LangStats
from nano_orchestrator.application.codegen_prompts import (
    build_orchestrator_prompt,
    build_worker_prompt,
    extract_code,
)
from nano_orchestrator.application.judge_use_case import JudgeUseCase
from nano_orchestrator.domain.entities import MicroTask, WorkerResponse
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter
from nano_orchestrator.infrastructure.sandbox import CompositeSandbox

GOLD = ROOT / "tests" / "golden" / "gold_set.json"
RESULTS = ROOT / "benchmarks" / "RESULTS.md"
ORCH_SAMPLES = ROOT / "benchmarks" / "orchestrator_samples.json"

_JSON_ARRAY_RE = re.compile(r"\[[\s\S]*\]")


def _load_gold_tasks() -> list[MicroTask]:
    raw = json.loads(GOLD.read_text(encoding="utf-8"))["tasks"]
    tasks: list[MicroTask] = []
    for item in raw:
        payload = {k: v for k, v in item.items() if k != "gold_code"}
        tasks.append(MicroTask.model_validate(payload))
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


def run_worker_bakeoff(
    *,
    model_id: str,
    base_url: str,
    limit: int | None,
) -> BakeoffSummary:
    adapter = LlamaCppAdapter(base_url)
    health = adapter.health()
    if health.is_err():
        raise RuntimeError(health.error)
    judge = JudgeUseCase(CompositeSandbox())
    tasks = _load_gold_tasks()
    if limit is not None:
        tasks = tasks[:limit]

    by_lang: dict[str, LangStats] = {
        "javascript": LangStats(),
        "html": LangStats(),
        "freemarker": LangStats(),
    }
    tps_samples: list[float] = []
    peak_vram = _vram_mb()

    for task in tasks:
        prompt = build_worker_prompt(task)
        gen = adapter.generate_detailed(prompt, max_tokens=task.max_tokens)
        stats = by_lang[task.language.value]
        stats.total += 1
        if gen.is_err():
            continue
        result = gen.value  # type: ignore[union-attr]
        stats.latencies_ms.append(result.latency_ms)
        if result.tokens_per_sec:
            tps_samples.append(result.tokens_per_sec)
        code = extract_code(result.text, task.language)
        response = WorkerResponse(
            task_id=task.id,
            code=code,
            confidence=0.5,
            latency_ms=result.latency_ms,
            tokens_used=result.tokens_predicted or max(1, len(code.split())),
        )
        verdict = judge.judge(task, response)
        if verdict.is_ok() and verdict.value.passed:  # type: ignore[union-attr]
            stats.passed += 1
        peak_vram = max(filter(None, [peak_vram, _vram_mb()]), default=peak_vram)

    return BakeoffSummary(
        model_id=model_id,
        role="worker" if model_id != "qwen25-coder-0.5b" else "baseline",
        by_lang=by_lang,
        vram_mb=peak_vram,
        tokens_per_sec=(statistics.median(tps_samples) if tps_samples else None),
        notes="measured via sandbox Pass@1",
    )


def _parse_microtasks(raw: str) -> list[dict]:
    text = raw.strip()
    for marker in ("<think>", "</think>"):
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    match = _JSON_ARRAY_RE.search(text)
    if not match:
        raise ValueError("no_json_array")
    data = json.loads(match.group(0))
    if not isinstance(data, list):
        raise ValueError("not_a_list")
    return data


def run_orchestrator_bakeoff(
    *,
    model_id: str,
    base_url: str,
    limit: int | None,
) -> BakeoffSummary:
    adapter = LlamaCppAdapter(base_url)
    health = adapter.health()
    if health.is_err():
        raise RuntimeError(health.error)
    samples = json.loads(ORCH_SAMPLES.read_text(encoding="utf-8"))["requests"]
    if limit is not None:
        samples = samples[:limit]

    valid = 0
    latencies: list[int] = []
    tps_samples: list[float] = []
    peak_vram = _vram_mb()

    for sample in samples:
        prompt = build_orchestrator_prompt(sample)
        gen = adapter.generate_detailed(prompt, max_tokens=768)
        if gen.is_err():
            continue
        result = gen.value  # type: ignore[union-attr]
        latencies.append(result.latency_ms)
        if result.tokens_per_sec:
            tps_samples.append(result.tokens_per_sec)
        try:
            items = _parse_microtasks(result.text)
            if not items or len(items) > 5:
                raise ValueError("bad_count")
            for item in items:
                MicroTask.model_validate(item)
            valid += 1
        except (ValueError, json.JSONDecodeError, Exception):
            pass
        peak_vram = max(filter(None, [peak_vram, _vram_mb()]), default=peak_vram)

    total = len(samples)
    # Encode JSON-valid rate into a single "javascript" column for RESULTS table reuse.
    stats = LangStats(passed=valid, total=total, latencies_ms=latencies)
    return BakeoffSummary(
        model_id=model_id,
        role="orchestrator",
        by_lang={"javascript": stats, "html": LangStats(), "freemarker": LangStats()},
        vram_mb=peak_vram,
        tokens_per_sec=(statistics.median(tps_samples) if tps_samples else None),
        notes=f"JSON-valid MicroTask rate {valid}/{total}",
    )


def _format_row(summary: BakeoffSummary) -> str:
    role = summary.role
    tps = f"{summary.tokens_per_sec:.1f}" if summary.tokens_per_sec else ""
    vram = str(summary.vram_mb) if summary.vram_mb is not None else ""
    return (
        f"| {summary.model_id} | {role} | {summary.pass_at_1('javascript')} | "
        f"{summary.pass_at_1('html')} | {summary.pass_at_1('freemarker')} | "
        f"{summary.p50_ms()} | {vram} | {tps} | {summary.notes} |"
    )


_MODEL_LABELS = {
    "qwen25-coder-0.5b": "Qwen2.5-Coder-0.5B",
    "qwen3-0.6b": "Qwen3-0.6B",
    "gemma3-270m": "Gemma3-270M",
    "smollm2-360m": "SmolLM2-360M",
    "smollm3-3b": "SmolLM3-3B",
    "nanbeige4.1-3b": "Nanbeige4.1-3B",
}


def write_results_row(summary: BakeoffSummary) -> None:
    label = _MODEL_LABELS.get(summary.model_id, summary.model_id)
    text = RESULTS.read_text(encoding="utf-8")
    tps = f"{summary.tokens_per_sec:.1f}" if summary.tokens_per_sec else ""
    vram = str(summary.vram_mb) if summary.vram_mb is not None else ""
    row = (
        f"| {label} | {summary.role} | {summary.pass_at_1('javascript')} | "
        f"{summary.pass_at_1('html')} | {summary.pass_at_1('freemarker')} | "
        f"{summary.p50_ms()} | {vram} | {tps} | {summary.notes} |"
    )
    lines = text.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"| {label} |"):
            out.append(row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        raise RuntimeError(f"RESULTS.md missing row for {label}")
    RESULTS.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Nano-orchestrator bake-off")
    parser.add_argument("--mode", choices=["worker", "orchestrator"], required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--write-results", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    if args.mode == "worker":
        summary = run_worker_bakeoff(
            model_id=args.model_id, base_url=args.base_url, limit=args.limit
        )
    else:
        summary = run_orchestrator_bakeoff(
            model_id=args.model_id, base_url=args.base_url, limit=args.limit
        )

    print(_format_row(summary))
    overall = summary.overall_pass()
    if overall is not None:
        print(f"overall_pass@1={overall:.3f}")
    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {
                    "model_id": summary.model_id,
                    "role": summary.role,
                    "pass_js": summary.pass_at_1("javascript"),
                    "pass_html": summary.pass_at_1("html"),
                    "pass_ftl": summary.pass_at_1("freemarker"),
                    "p50_ms": summary.p50_ms(),
                    "vram_mb": summary.vram_mb,
                    "tokens_per_sec": summary.tokens_per_sec,
                    "notes": summary.notes,
                    "overall": overall,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    if args.write_results:
        write_results_row(summary)
        print(f"updated {RESULTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
