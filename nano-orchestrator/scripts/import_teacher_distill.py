#!/usr/bin/env python3
"""T-051 — Top up train JSONL from parent teacher-distilled datasets (no held_out leak)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.application.train_export import (  # noqa: E402
    DEFAULT_N_MIN,
    LANGS,
    counts_meet_n,
    dedupe_examples,
    examples_from_teacher_jsonl,
    filter_held_out,
    group_by_language,
    load_jsonl,
    write_jsonl,
)
from nano_orchestrator.domain.held_out_leak import load_held_out_blocklist  # noqa: E402
from nano_orchestrator.domain.train_example import TrainExample  # noqa: E402

DEFAULT_PARENT = {
    "javascript": REPO
    / "data"
    / "datasets"
    / "ds-2026-06-21-js-m2000-v2"
    / "examples.jsonl",
    "html": REPO
    / "data"
    / "datasets"
    / "ds-2026-06-21-html-m2000-v2"
    / "examples.jsonl",
    "freemarker": REPO
    / "data"
    / "datasets"
    / "ds-2026-06-21-fmt-m2000-v2"
    / "examples.jsonl",
}


def _load_existing(path: Path) -> list[TrainExample]:
    if not path.is_file():
        return []
    return [TrainExample.model_validate(row) for row in load_jsonl(path)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-dir", type=Path, default=ROOT / "data" / "train")
    parser.add_argument(
        "--held-out",
        type=Path,
        default=ROOT / "tests" / "golden" / "held_out.json",
    )
    parser.add_argument("--n-min", type=int, default=DEFAULT_N_MIN)
    parser.add_argument(
        "--per-language-cap",
        type=int,
        default=200,
        help="Max teacher rows to consider per language",
    )
    args = parser.parse_args()

    blocked = load_held_out_blocklist(args.held_out)
    all_examples: list[TrainExample] = []
    for lang in LANGS:
        existing = _load_existing(args.train_dir / lang / "train.jsonl")
        need = max(0, args.n_min - len(existing))
        teacher_path = DEFAULT_PARENT[lang]
        if not teacher_path.is_file():
            print(f"ERROR: missing parent dataset {teacher_path}", file=sys.stderr)
            return 1
        # Fetch enough to cover need after dedupe (pull buffer).
        pull = max(need * 3, args.n_min, 1)
        pull = min(pull, args.per_language_cap)
        teacher = examples_from_teacher_jsonl(
            teacher_path, language=lang, blocked=blocked, limit=pull
        )
        merged = dedupe_examples(existing + teacher)
        merged, _ = filter_held_out(merged, args.held_out)
        # Prefer keeping existing first; trim to cap after meeting N.
        if len(merged) > args.per_language_cap:
            merged = merged[: args.per_language_cap]
        write_jsonl(args.train_dir / lang / "train.jsonl", merged)
        all_examples.extend(merged)

    grouped = group_by_language(all_examples)
    summary = {lang: len(grouped.get(lang, [])) for lang in LANGS}
    manifest = {
        "n_min": args.n_min,
        "counts": summary,
        "meets_n": counts_meet_n(grouped, args.n_min),
        "held_out_leak_check": True,
        "teacher_sources": {k: str(v) for k, v in DEFAULT_PARENT.items()},
    }
    args.train_dir.mkdir(parents=True, exist_ok=True)
    (args.train_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    return 0 if manifest["meets_n"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
