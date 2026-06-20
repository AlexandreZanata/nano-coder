#!/usr/bin/env python3
"""Run Stage 3 promotion gates and publish seeds to data/seeds/ (BR-001, BR-003, BR-004)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.scope_boundary import load_scope_boundary  # noqa: E402
from nano_coder.domain.seed_promotion import (  # noqa: E402
    QualityGateType,
    build_manifest,
    load_seed_records,
    run_promotion_gates,
    write_promoted_seeds,
)
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy  # noqa: E402

DEFAULT_TAXONOMY = ROOT / "config" / "seeds-v1" / "taxonomy.yaml"
DEFAULT_SCOPE = ROOT / "config" / "scope-boundary.yaml"
DEFAULT_ESLINT = ROOT / "config" / "eslint" / "eslint.config.js"
DEFAULT_OUTPUT = ROOT / "data" / "seeds"
DEFAULT_MANIFEST = ROOT / "data" / "seeds" / "manifest.json"
DEFAULT_REPORT = ROOT / ".local" / "review" / "promotion-report.json"


def _collect_draft_records(draft_root: Path) -> list[dict]:
    records: list[dict] = []
    for language_dir in ("javascript", "html", "freemarker"):
        folder = draft_root / language_dir
        if folder.is_dir():
            records.extend(load_seed_records(folder))
    if not records and draft_root.is_dir():
        records = load_seed_records(draft_root)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote gold seeds after quality gates")
    parser.add_argument("--draft", type=Path, help="Draft seed root (.local/seeds/draft)")
    parser.add_argument("--verify", type=Path, help="Verify promoted seeds directory in place")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--eslint-config", type=Path, default=DEFAULT_ESLINT)
    parser.add_argument("--skip-lint", action="store_true")
    parser.add_argument("--seed-set-version", default="seeds-v1")
    args = parser.parse_args()

    if args.verify:
        records = []
        for folder in ("javascript", "html", "freemarker"):
            records.extend(load_seed_records(args.verify / folder))
    elif args.draft:
        records = _collect_draft_records(args.draft)
    else:
        parser.error("provide --draft or --verify")

    taxonomy = load_seed_taxonomy(args.taxonomy)
    scope = load_scope_boundary(args.scope)

    gates_run = [
        QualityGateType.SCHEMA,
        QualityGateType.SYNTAX,
        QualityGateType.HELD_OUT,
        QualityGateType.DUPLICATE,
    ]
    if not args.skip_lint:
        gates_run.insert(2, QualityGateType.LINT)

    result = run_promotion_gates(
        records,
        taxonomy=taxonomy,
        scope=scope,
        eslint_config=args.eslint_config if not args.skip_lint else None,
        skip_lint=args.skip_lint,
    )

    report = {
        "passed": result.passed,
        "seedCount": result.seed_count,
        "countsByLanguage": result.counts_by_language,
        "failures": [
            {"seedId": f.seed_id, "gate": f.gate, "message": f.message} for f in result.failures
        ],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if not result.passed:
        for failure in result.failures:
            print(f"{failure.gate} [{failure.seed_id}]: {failure.message}", file=sys.stderr)
        print(f"FAILED: {len(result.failures)} gate failure(s)", file=sys.stderr)
        return 1

    if args.draft and not args.verify:
        write_promoted_seeds(records, args.output)

    manifest = build_manifest(
        result,
        seed_set_version=args.seed_set_version,
        scope_version=scope.version,
        taxonomy_version=taxonomy.version,
        gates_run=[gate.value for gate in gates_run],
    )
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"OK: {result.seed_count} seed(s) promoted — manifest {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
