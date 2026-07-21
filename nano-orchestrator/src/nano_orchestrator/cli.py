"""CLI entrypoint — `nano-orchestrator` console script."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run_script(rel: str, extra: list[str]) -> int:
    script = ROOT / rel
    cmd = [sys.executable, str(script), *extra]
    return subprocess.call(cmd, cwd=str(ROOT))


def cmd_test(_: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, "-m", "pytest", "tests/unit", "-q"],
        cwd=str(ROOT),
    )


def cmd_validate_schema(_: argparse.Namespace) -> int:
    return _run_script("scripts/validate_schema.py", [])


def cmd_smoke(args: argparse.Namespace) -> int:
    extra = ["--request", args.request]
    if args.fixed_tasks:
        extra.append("--fixed-tasks")
    if args.static_routing:
        extra.append("--static-routing")
    if args.no_manage_server:
        extra.append("--no-manage-server")
    return _run_script("scripts/smoke_runner.py", extra)


def cmd_bakeoff(args: argparse.Namespace) -> int:
    extra = [
        "--mode",
        args.mode,
        "--model-id",
        args.model_id,
        "--base-url",
        args.base_url,
    ]
    if args.write_results:
        extra.append("--write-results")
    if args.limit is not None:
        extra.extend(["--limit", str(args.limit)])
    return _run_script("benchmarks/worker_bakeoff.py", extra)


def cmd_gates(args: argparse.Namespace) -> int:
    extra: list[str] = []
    if args.limit is not None:
        extra.extend(["--limit", str(args.limit)])
    return _run_script("benchmarks/run_success_gates.py", extra)


def cmd_large_site(args: argparse.Namespace) -> int:
    extra: list[str] = []
    if args.skip_orchestrator:
        extra.append("--skip-orchestrator")
    if args.schedule:
        extra.extend(["--schedule", args.schedule])
    if getattr(args, "keep_alive", False):
        extra.append("--keep-alive")
    if getattr(args, "no_keep_alive", False):
        extra.append("--no-keep-alive")
    if getattr(args, "port", None) is not None:
        extra.extend(["--port", str(args.port)])
    if getattr(args, "base_url", None):
        extra.extend(["--base-url", args.base_url])
    return _run_script("benchmarks/run_large_site_schedule.py", extra)


def cmd_arena(args: argparse.Namespace) -> int:
    script = ROOT / "arena" / "server.py"
    cmd = [
        sys.executable,
        str(script),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    return subprocess.call(cmd, cwd=str(ROOT))



def cmd_decompose(args: argparse.Namespace) -> int:
    """Validate MicroTask JSON (offline) or live-decompose via smoke fixed path."""
    from nano_orchestrator.domain.microtask_parser import parse_microtasks_json

    if args.json_file:
        raw = Path(args.json_file).read_text(encoding="utf-8")
        result = parse_microtasks_json(raw)
        if result.is_err():
            print(json.dumps({"ok": False, "error": result.error}))
            return 1
        tasks = result.value  # type: ignore[union-attr]
        print(
            json.dumps(
                {
                    "ok": True,
                    "count": len(tasks),
                    "tasks": [t.model_dump(mode="json") for t in tasks],
                },
                indent=2,
            )
        )
        return 0
    if args.request:
        # Live path: full smoke with LLM decompose (needs server unless fixed-tasks)
        extra = ["--request", args.request]
        if args.fixed_tasks:
            extra.append("--fixed-tasks")
        if args.no_manage_server:
            extra.append("--no-manage-server")
        return _run_script("scripts/smoke_runner.py", extra)
    print("decompose: provide --json-file or --request", file=sys.stderr)
    return 2


def cmd_judge(args: argparse.Namespace) -> int:
    """Sandbox-first judge for one MicroTask + code file (CPU)."""
    from nano_orchestrator.application.judge_use_case import JudgeUseCase
    from nano_orchestrator.domain.entities import (
        MicroTask,
        TargetLanguage,
        WorkerResponse,
        WorkerRole,
    )
    from nano_orchestrator.infrastructure.sandbox import CompositeSandbox

    code = Path(args.code_file).read_text(encoding="utf-8")
    language = TargetLanguage(args.language)
    acceptance = [a.strip() for a in args.acceptance.split(",") if a.strip()]
    task = MicroTask(
        id=args.task_id,
        role=WorkerRole.CODER,
        language=language,
        prompt=args.prompt or "judge CLI",
        acceptance=acceptance or ["syntax_valid"],
    )
    response = WorkerResponse(
        task_id=args.task_id,
        code=code,
        confidence=0.5,
        latency_ms=0,
        tokens_used=max(1, len(code) // 4),
    )
    judged = JudgeUseCase(CompositeSandbox()).judge(task, response)
    if judged.is_err():
        print(json.dumps({"ok": False, "error": judged.error}))
        return 1
    verdict = judged.value  # type: ignore[union-attr]
    print(json.dumps({"ok": True, "verdict": verdict.model_dump(mode="json")}, indent=2))
    return 0 if verdict.passed else 1


def cmd_version(_: argparse.Namespace) -> int:
    from importlib.metadata import PackageNotFoundError, version

    try:
        ver = version("nano-orchestrator")
    except PackageNotFoundError:
        ver = "0.1.0"
    print(json.dumps({"name": "nano-orchestrator", "version": ver}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nano-orchestrator",
        description="Local Orchestrator–Workers–Judge tooling (research; GATE-NEG keep solo 0.5B)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_test = sub.add_parser("test", help="Run unit tests")
    p_test.set_defaults(func=cmd_test)

    p_schema = sub.add_parser("validate-schema", help="Validate gold JSON schemas")
    p_schema.set_defaults(func=cmd_validate_schema)

    p_smoke = sub.add_parser("smoke", help="E2E smoke (needs llama-server unless fixed path)")
    p_smoke.add_argument("--request", required=True)
    p_smoke.add_argument("--fixed-tasks", action="store_true")
    p_smoke.add_argument("--static-routing", action="store_true")
    p_smoke.add_argument("--no-manage-server", action="store_true")
    p_smoke.set_defaults(func=cmd_smoke)

    p_dec = sub.add_parser(
        "decompose",
        help="Validate MicroTask JSON (--json-file) or live smoke (--request)",
    )
    p_dec.add_argument("--json-file", default=None)
    p_dec.add_argument("--request", default=None)
    p_dec.add_argument("--fixed-tasks", action="store_true")
    p_dec.add_argument("--no-manage-server", action="store_true")
    p_dec.set_defaults(func=cmd_decompose)

    p_judge = sub.add_parser("judge", help="Sandbox-first judge for one code file")
    p_judge.add_argument("--task-id", default="cli-task")
    p_judge.add_argument(
        "--language",
        choices=["javascript", "html", "freemarker", "css"],
        required=True,
    )
    p_judge.add_argument("--code-file", required=True)
    p_judge.add_argument("--prompt", default="")
    p_judge.add_argument("--acceptance", default="syntax_valid")
    p_judge.set_defaults(func=cmd_judge)

    p_bake = sub.add_parser("bakeoff", help="Worker/orchestrator bake-off")
    p_bake.add_argument("--mode", choices=["worker", "orchestrator"], default="worker")
    p_bake.add_argument("--model-id", default="qwen25-coder-0.5b")
    p_bake.add_argument("--base-url", default="http://127.0.0.1:8081")
    p_bake.add_argument("--write-results", action="store_true")
    p_bake.add_argument("--limit", type=int, default=None)
    p_bake.set_defaults(func=cmd_bakeoff)

    p_gates = sub.add_parser("gates", help="Run EG success gates (GPU)")
    p_gates.add_argument("--limit", type=int, default=None)
    p_gates.set_defaults(func=cmd_gates)

    p_site = sub.add_parser(
        "large-site",
        help="Multi-model large-site schedule (one model per task)",
    )
    p_site.add_argument("--skip-orchestrator", action="store_true")
    p_site.add_argument("--schedule", default=None)
    p_site.add_argument(
        "--keep-alive",
        action="store_true",
        help="Reuse server across consecutive same-model worker slots",
    )
    p_site.add_argument(
        "--no-keep-alive",
        action="store_true",
        help="Disable keep-alive even if schedule enables it",
    )
    p_site.add_argument(
        "--port",
        type=int,
        default=None,
        help="llama-server port (default: runner 8081)",
    )
    p_site.add_argument(
        "--base-url",
        default=None,
        help="llama-server base URL (default: http://127.0.0.1:<port>)",
    )
    p_site.set_defaults(func=cmd_large_site)

    p_arena = sub.add_parser("arena", help="Open local Arena playground (proposals + runs)")
    p_arena.add_argument("--host", default="127.0.0.1")
    p_arena.add_argument("--port", type=int, default=8765)
    p_arena.set_defaults(func=cmd_arena)

    p_ver = sub.add_parser("version", help="Print package version")
    p_ver.set_defaults(func=cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
