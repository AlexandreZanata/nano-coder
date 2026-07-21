#!/usr/bin/env python3
"""T-053 — Merge adapter → GGUF Q4_K_M and register for llama-server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.infrastructure.gguf_export import (  # noqa: E402
    export_worker_gguf,
    register_in_bonsai_models,
    register_in_orchestrator_config,
)
from nano_orchestrator.infrastructure.qlora_trainer import HF_BASE_MODELS  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--language",
        required=True,
        choices=["javascript", "html", "freemarker"],
    )
    parser.add_argument(
        "--adapter-dir",
        type=Path,
        default=None,
        help="Defaults to data/checkpoints/worker-<lang>-qlora-smoke/adapter",
    )
    parser.add_argument("--base-worker", default="qwen25-coder-0.5b")
    parser.add_argument(
        "--export-root",
        type=Path,
        default=ROOT / "data" / "gguf",
    )
    parser.add_argument(
        "--bonsai-models",
        type=Path,
        default=REPO / ".local" / "bonsai-chat" / "models.json",
    )
    parser.add_argument(
        "--orch-config",
        type=Path,
        default=ROOT / "config" / "fine_tuned_workers.json",
    )
    parser.add_argument("--skip-register", action="store_true")
    args = parser.parse_args()

    adapter = args.adapter_dir or (
        ROOT / "data" / "checkpoints" / f"worker-{args.language}-qlora-smoke" / "adapter"
    )
    if not adapter.is_dir():
        print(f"ERROR: adapter missing: {adapter}", file=sys.stderr)
        return 1
    base_hf = HF_BASE_MODELS[args.base_worker]
    result = export_worker_gguf(
        language=args.language,
        base_hf_id=base_hf,
        adapter_dir=adapter,
        export_root=args.export_root,
    )
    if not args.skip_register:
        if args.bonsai_models.is_file():
            register_in_bonsai_models(
                models_json=args.bonsai_models,
                model_id=result.model_id,
                gguf_path=result.q4_gguf,
                label=f"Qwen2.5-Coder-0.5B {args.language} FT Q4_K_M",
            )
        register_in_orchestrator_config(
            config_path=args.orch_config,
            language=args.language,
            model_id=result.model_id,
            gguf_path=REPO
            / ".local"
            / "models"
            / result.model_id
            / result.q4_gguf.name,
        )
    print(
        json.dumps(
            {
                "model_id": result.model_id,
                "q4_gguf": str(result.q4_gguf),
                "merged_dir": str(result.merged_dir),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
