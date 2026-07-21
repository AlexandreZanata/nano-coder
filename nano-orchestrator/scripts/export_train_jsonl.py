#!/usr/bin/env python3
"""T-050 — Export Judge-approved / gold / proposal pairs → per-language train JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.train_export import (  # noqa: E402
    DEFAULT_N_MIN,
    LANGS,
    counts_meet_n,
    dedupe_examples,
    examples_from_gold,
    examples_from_judge_log,
    examples_from_proposal,
    filter_held_out,
    group_by_language,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "data" / "train",
        help="Directory for per-language train.jsonl",
    )
    parser.add_argument(
        "--gold",
        type=Path,
        default=ROOT / "tests" / "golden" / "gold_set.json",
    )
    parser.add_argument(
        "--held-out",
        type=Path,
        default=ROOT / "tests" / "golden" / "held_out.json",
    )
    parser.add_argument(
        "--proposal-dir",
        type=Path,
        default=ROOT / "out" / "proposal",
    )
    parser.add_argument(
        "--judge-log",
        type=Path,
        default=ROOT / "logs" / "judge_approved.jsonl",
    )
    parser.add_argument("--n-min", type=int, default=DEFAULT_N_MIN)
    args = parser.parse_args()

    examples = []
    examples.extend(examples_from_gold(args.gold))
    examples.extend(examples_from_proposal(args.proposal_dir))
    examples.extend(examples_from_judge_log(args.judge_log))
    examples = dedupe_examples(examples)
    examples, dropped = filter_held_out(examples, args.held_out)

    grouped = group_by_language(examples)
    summary: dict[str, int] = {}
    for lang in LANGS:
        path = args.out_dir / lang / "train.jsonl"
        summary[lang] = write_jsonl(path, grouped.get(lang, []))

    manifest = {
        "n_min": args.n_min,
        "counts": summary,
        "held_out_dropped": dropped,
        "meets_n": counts_meet_n(grouped, args.n_min),
        "sources": ["gold_seed", "proposal", "judge_log"],
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    if not manifest["meets_n"]:
        print(
            f"WARN: counts below N={args.n_min}; run import_teacher_distill.py (T-051)",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
