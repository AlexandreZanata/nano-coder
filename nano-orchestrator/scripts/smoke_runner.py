#!/usr/bin/env python3
"""Phase 2 end-to-end smoke: Orchestrator → Workers → Judge → proposal.

Usage:
  python scripts/smoke_runner.py --request "Create a JS clamp and an HTML submit form"
  python scripts/smoke_runner.py --request "..." --fixed-tasks   # skip orch LLM
  python scripts/smoke_runner.py --request "..." --no-manage-server --base-url http://127.0.0.1:8081
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.pipeline import OrchestrationPipeline, PipelineConfig
from nano_orchestrator.application.worker_dispatch import WorkerRouting
from nano_orchestrator.domain.entities import MicroTask, TargetLanguage, WorkerRole


def _fixed_tasks() -> list[MicroTask]:
    return [
        MicroTask(
            id="smoke-js",
            role=WorkerRole.CODER,
            language=TargetLanguage.JAVASCRIPT,
            prompt=(
                "Export function clamp(n, min, max) that bounds n to [min, max]. "
                "Throw RangeError if min > max. Use ES modules."
            ),
            constraints=["ES modules", "no var"],
            acceptance=["syntax_valid"],
            max_tokens=160,
        ),
        MicroTask(
            id="smoke-html",
            role=WorkerRole.CODER,
            language=TargetLanguage.HTML,
            prompt=(
                "Write a form method=post action=/checkout with a Submit button type=submit. "
                "No inline scripts."
            ),
            constraints=["semantic HTML5"],
            acceptance=["syntax_valid"],
            max_tokens=128,
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Nano-orchestrator E2E smoke")
    parser.add_argument("--request", required=True)
    parser.add_argument(
        "--fixed-tasks",
        action="store_true",
        help="Use deterministic MicroTasks (still runs live workers)",
    )
    parser.add_argument("--no-manage-server", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "out")
    parser.add_argument("--orchestrator-model", default="smollm3-3b")
    args = parser.parse_args()

    config = PipelineConfig(
        orchestrator_model=args.orchestrator_model,
        routing=WorkerRouting(),
        base_url=args.base_url,
        port=args.port,
        out_dir=args.out_dir,
        manage_server=not args.no_manage_server,
    )
    pipeline = OrchestrationPipeline(config)
    fixed = _fixed_tasks() if args.fixed_tasks else None
    result = pipeline.run(args.request, fixed_tasks=fixed)
    if result.is_err():
        print(json.dumps({"ok": False, "error": result.error}, indent=2))
        return 1
    payload = result.value  # type: ignore[union-attr]
    summary = {
        "ok": True,
        "request": args.request,
        "package": str(payload.package_path),
        "peak_vram_mb": payload.peak_vram_mb,
        "vram_ok": payload.vram_ok,
        "tasks": [t.model_dump(mode="json") for t in payload.tasks],
        "escalate_to_human": payload.escalate,
        "verdicts": {
            tid: v.model_dump(mode="json") for tid, v in payload.verdicts.items()
        },
    }
    print(json.dumps(summary, indent=2))
    print("\nHUMAN GATE: review out/proposal/ — do not auto-persist to product paths.")
    return 0 if payload.vram_ok else 2


if __name__ == "__main__":
    sys.exit(main())
