#!/usr/bin/env python3
"""Validate GoldSeedExample JSON files (schema, taxonomy, BR-004 scope)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.gold_seed_example import (  # noqa: E402
    SeedValidationError,
    validate_gold_seed,
)
from nano_coder.domain.scope_boundary import load_scope_boundary  # noqa: E402
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy  # noqa: E402

DEFAULT_TAXONOMY = ROOT / "config" / "seeds-v1" / "taxonomy.yaml"
DEFAULT_SCOPE = ROOT / "config" / "scope-boundary.yaml"


def load_records(path: Path) -> list[dict]:
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
    parser = argparse.ArgumentParser(description="Validate GoldSeedExample seed files")
    parser.add_argument("path", type=Path, help="Seed JSON file, JSONL, or directory")
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--skip-scope", action="store_true", help="Skip BR-004 held-out leak check")
    parser.add_argument(
        "--require-metadata",
        action="store_true",
        help="Require metadata block (promoted seeds in data/seeds/)",
    )
    args = parser.parse_args()

    taxonomy = load_seed_taxonomy(args.taxonomy)
    scope = None if args.skip_scope else load_scope_boundary(args.scope)
    records = load_records(args.path)
    errors: list[str] = []

    for record in records:
        try:
            validate_gold_seed(
                record,
                taxonomy,
                scope=scope,
                require_metadata=args.require_metadata,
            )
        except SeedValidationError as exc:
            errors.append(str(exc))

    if errors:
        for message in errors:
            print(message, file=sys.stderr)
        return 1

    print(f"OK: {len(records)} seed(s) passed validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
