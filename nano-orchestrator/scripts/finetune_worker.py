#!/usr/bin/env python3
"""T-052 — QLoRA smoke fine-tune for one TargetLanguage worker."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.infrastructure.qlora_trainer import run_qlora_smoke  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--language",
        required=True,
        choices=["javascript", "html", "freemarker"],
    )
    parser.add_argument(
        "--train-jsonl",
        type=Path,
        default=None,
        help="Defaults to data/train/<language>/train.jsonl",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "data" / "checkpoints",
    )
    parser.add_argument("--base-worker", default="qwen25-coder-0.5b")
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=4)
    args = parser.parse_args()

    train_jsonl = args.train_jsonl or (
        ROOT / "data" / "train" / args.language / "train.jsonl"
    )
    if not train_jsonl.is_file():
        print(f"ERROR: missing {train_jsonl} — run export + teacher import", file=sys.stderr)
        return 1

    result = run_qlora_smoke(
        language=args.language,
        train_jsonl=train_jsonl,
        output_root=args.output_root,
        base_worker_id=args.base_worker,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        grad_accum=args.grad_accum,
    )
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "language": result.language,
                "adapter_dir": str(result.adapter_dir),
                "steps": result.steps,
                "example_count": result.example_count,
                "peak_vram_mb": result.peak_vram_mb,
                "train_loss": result.train_loss,
                "elapsed_s": result.elapsed_s,
            },
            indent=2,
        )
    )
    if result.peak_vram_mb is not None and result.peak_vram_mb > 7500:
        print("WARN: peak VRAM near 8GB ceiling", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
