#!/usr/bin/env python3
"""Validate examples against scope boundary and held-out isolation (BR-004)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.scope_boundary import (  # noqa: E402
    HeldOutLeakDetected,
    detect_held_out_leak,
    load_scope_boundary,
)
from nano_coder.domain.target_language import TargetLanguage  # noqa: E402

DEFAULT_SCOPE = ROOT / "config" / "scope-boundary.yaml"


def load_examples(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        text = path.read_text(encoding="utf-8")
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if path.is_dir():
        records: list[dict] = []
        for file in sorted(path.rglob("*.json")):
            records.append(json.loads(file.read_text(encoding="utf-8")))
        return records
    return [json.loads(path.read_text(encoding="utf-8"))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scope boundary / BR-004 leakage")
    parser.add_argument("path", type=Path, help="Seed file, JSONL, or directory")
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    args = parser.parse_args()

    scope = load_scope_boundary(args.scope)
    examples = load_examples(args.path)
    violations: list[str] = []

    for example in examples:
        example_id = example.get("id", "<unknown>")
        instruction = example.get("instruction", "")
        code = example.get("code", "")
        topic_id = example.get("topicId")
        lang_raw = example.get("targetLanguage")
        target_language = TargetLanguage(lang_raw) if lang_raw else None
        try:
            detect_held_out_leak(
                scope,
                example_id=example_id,
                instruction=instruction,
                code=code,
                topic_id=topic_id,
                target_language=target_language,
            )
        except HeldOutLeakDetected as exc:
            violations.append(str(exc))

    if violations:
        for message in violations:
            print(message, file=sys.stderr)
        return 1

    print(f"OK: {len(examples)} example(s) passed scope boundary check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
