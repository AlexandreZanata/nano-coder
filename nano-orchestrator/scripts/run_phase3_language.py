#!/usr/bin/env python3
"""Run Phase 3 specialize pipeline for one language: train → GGUF → held_out score."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = Path(sys.executable)
SCORE_PY = ROOT / "scripts" / "score_held_out.py"


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def _restart_model(model_id: str) -> None:
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
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode or 1)


def _load_score_module():
    spec = importlib.util.spec_from_file_location("score_held_out", SCORE_PY)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--language",
        required=True,
        choices=["javascript", "html", "freemarker"],
    )
    parser.add_argument("--max-steps", type=int, default=40)
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--skip-score", action="store_true")
    parser.add_argument("--base-model-id", default="qwen25-coder-0.5b")
    args = parser.parse_args()

    ft_model_id = f"qwen25-coder-0.5b-{args.language}-ft"
    score_mod = _load_score_module()

    if not args.skip_train:
        _run(
            [
                str(PY),
                "scripts/finetune_worker.py",
                "--language",
                args.language,
                "--max-steps",
                str(args.max_steps),
            ]
        )
    if not args.skip_export:
        _run([str(PY), "scripts/export_worker_gguf.py", "--language", args.language])

    if args.skip_score:
        print(json.dumps({"language": args.language, "ft_model_id": ft_model_id}))
        return 0

    tasks = score_mod._load_held_out(
        ROOT / "tests" / "golden" / "held_out.json", args.language
    )
    _restart_model(args.base_model_id)
    base = score_mod._score(
        model_id=args.base_model_id, base_url="http://127.0.0.1:8081", tasks=tasks
    )
    _restart_model(ft_model_id)
    ft = score_mod._score(
        model_id=ft_model_id, base_url="http://127.0.0.1:8081", tasks=tasks
    )
    gate = ft["pass_at_1"] >= base["pass_at_1"]
    merged = {
        "language": args.language,
        "base": base,
        "ft": ft,
        "gate_pass_at_1_not_worse": gate,
    }
    out = ROOT / "benchmarks" / "runs" / f"held_out_{args.language}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    score_mod._append_results_table(
        ROOT / "benchmarks" / "RESULTS.md",
        language=args.language,
        base_id=args.base_model_id,
        base_pass=base["pass_at_1"],
        ft_id=ft_model_id,
        ft_pass=ft["pass_at_1"],
        gate=gate,
    )
    print(json.dumps(merged, indent=2))
    return 0 if gate else 3


if __name__ == "__main__":
    raise SystemExit(main())
