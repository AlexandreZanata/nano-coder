#!/usr/bin/env python3
"""T-054 — Score base vs fine-tuned worker on held_out.json (sandbox Pass@1)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.codegen_prompts import (  # noqa: E402
    build_worker_prompt,
    extract_code,
)
from nano_orchestrator.application.judge_use_case import JudgeUseCase  # noqa: E402
from nano_orchestrator.domain.entities import (  # noqa: E402
    MicroTask,
    TargetLanguage,
    WorkerResponse,
    WorkerRole,
)
from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter  # noqa: E402
from nano_orchestrator.infrastructure.sandbox import CompositeSandbox  # noqa: E402


def _load_held_out(path: Path, language: str | None) -> list[MicroTask]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    tasks: list[MicroTask] = []
    for raw in payload["tasks"]:
        if language and raw["language"] != language:
            continue
        tasks.append(
            MicroTask(
                id=raw["id"],
                role=WorkerRole.CODER,
                language=TargetLanguage(raw["language"]),
                prompt=raw["prompt"],
                constraints=list(raw.get("constraints") or []),
                acceptance=list(raw.get("acceptance") or ["syntax_valid"]),
                max_tokens=int(raw.get("max_tokens") or 256),
            )
        )
    return tasks


def _score(
    *,
    model_id: str,
    base_url: str,
    tasks: list[MicroTask],
) -> dict:
    adapter = LlamaCppAdapter(base_url, model_id=model_id)
    health = adapter.health()
    if health.is_err():
        raise RuntimeError(health.error)
    judge = JudgeUseCase(CompositeSandbox())
    passed = 0
    rows = []
    for task in tasks:
        gen = adapter.generate_detailed(
            build_worker_prompt(task), max_tokens=task.max_tokens
        )
        if gen.is_err():
            rows.append({"task_id": task.id, "passed": False, "error": gen.error})
            continue
        result = gen.value  # type: ignore[union-attr]
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
        rows.append(
            {
                "task_id": task.id,
                "language": task.language.value,
                "passed": bool(ok),
                "score": None if verdict.is_err() else verdict.value.score,  # type: ignore[union-attr]
            }
        )
    total = len(tasks) or 1
    return {
        "model_id": model_id,
        "pass_at_1": round(passed / total, 4),
        "passed": passed,
        "total": len(tasks),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--base-model-id", default="qwen25-coder-0.5b")
    parser.add_argument("--ft-model-id", required=True)
    parser.add_argument(
        "--held-out",
        type=Path,
        default=ROOT / "tests" / "golden" / "held_out.json",
    )
    parser.add_argument(
        "--language",
        choices=["javascript", "html", "freemarker"],
        default=None,
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "runs" / "held_out_ft.json",
    )
    parser.add_argument(
        "--results-md",
        type=Path,
        default=ROOT / "benchmarks" / "RESULTS.md",
    )
    parser.add_argument(
        "--only-ft",
        action="store_true",
        help="Score only FT model (base row already known)",
    )
    args = parser.parse_args()

    tasks = _load_held_out(args.held_out, args.language)
    if not tasks:
        print("ERROR: no held_out tasks", file=sys.stderr)
        return 1

    payload: dict = {"language_filter": args.language, "comparisons": []}
    if not args.only_ft:
        print(f"Scoring base {args.base_model_id} …", file=sys.stderr)
        base = _score(model_id=args.base_model_id, base_url=args.base_url, tasks=tasks)
        payload["comparisons"].append(base)
    print(f"Scoring FT {args.ft_model_id} …", file=sys.stderr)
    ft = _score(model_id=args.ft_model_id, base_url=args.base_url, tasks=tasks)
    payload["comparisons"].append(ft)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if len(payload["comparisons"]) >= 2:
        base_p = payload["comparisons"][0]["pass_at_1"]
        ft_p = payload["comparisons"][1]["pass_at_1"]
        gate = ft_p >= base_p
        payload["gate_pass_at_1_not_worse"] = gate
        _append_results_table(
            args.results_md,
            language=args.language or "all",
            base_id=args.base_model_id,
            base_pass=base_p,
            ft_id=args.ft_model_id,
            ft_pass=ft_p,
            gate=gate,
        )
        print(json.dumps(payload, indent=2))
        return 0 if gate else 3

    print(json.dumps(payload, indent=2))
    return 0


def _append_results_table(
    path: Path,
    *,
    language: str,
    base_id: str,
    base_pass: float,
    ft_id: str,
    ft_pass: float,
    gate: bool,
) -> None:
    header = (
        "## Phase 3 held_out fine-tune\n\n"
        "| Language | Base model | Base Pass@1 | FT model | FT Pass@1 | Gate (≥ base) |\n"
        "|----------|------------|-------------|----------|-----------|---------------|\n"
    )
    row = (
        f"| {language} | {base_id} | {base_pass:.2f} | {ft_id} | {ft_pass:.2f} | "
        f"{'PASS' if gate else 'FAIL'} |\n"
    )
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    marker = "## Phase 3 held_out fine-tune"
    if marker not in text:
        path.write_text(text.rstrip() + "\n\n" + header + row, encoding="utf-8")
        return

    start = text.index(marker)
    rest = text[start:]
    next_h = rest.find("\n## ", 1)
    section = rest if next_h == -1 else rest[:next_h]
    tail = "" if next_h == -1 else rest[next_h:]
    lines = section.splitlines(keepends=True)
    # Keep header lines; replace language row if present.
    out_lines: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"| {language} |"):
            out_lines.append(row)
            replaced = True
        else:
            out_lines.append(line)
    if not replaced:
        if out_lines and not out_lines[-1].endswith("\n"):
            out_lines[-1] += "\n"
        out_lines.append(row)
    new_section = "".join(out_lines)
    if not new_section.endswith("\n"):
        new_section += "\n"
    path.write_text(text[:start] + new_section + (tail[1:] if tail.startswith("\n") else tail), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
