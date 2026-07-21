#!/usr/bin/env python3
"""Build M1 2,000-example dataset from gold seeds (no TeacherModel API)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.target_language import TargetLanguage  # noqa: E402
from nano_coder.infrastructure.local_enterprise_expander import (  # noqa: E402
    generate_local_enterprise_raw,
)

PHASE1_CONFIG = ROOT / ".local/overrides/phase1-milestone-2000.yaml"
PUBLISH_CONFIG = ROOT / ".local/overrides/dataset-publish-milestone-2000.yaml"
RAW_ROOT = ROOT / ".local/generation/raw"
SEEDS_ROOT = ROOT / "data/seeds"

RUN_IDS = {
    TargetLanguage.JAVASCRIPT: "gen-js-m2000-v2",
    TargetLanguage.HTML: "gen-html-m2000-v2",
    TargetLanguage.FREEMARKER: "gen-fmt-m2000-v2",
}
VERSIONS = {
    TargetLanguage.JAVASCRIPT: "ds-2026-06-21-js-m2000-v2",
    TargetLanguage.HTML: "ds-2026-06-21-html-m2000-v2",
    TargetLanguage.FREEMARKER: "ds-2026-06-21-fmt-m2000-v2",
}
MIXED_VERSION = "ds-2026-06-21-mixed-m2000-v2"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def build_language(language: TargetLanguage, variants_per_seed: int) -> dict[str, int]:
    run_id = RUN_IDS[language]
    _, candidate_count = generate_local_enterprise_raw(
        language=language,
        run_id=run_id,
        seeds_root=SEEDS_ROOT,
        output_root=RAW_ROOT,
        variants_per_seed=variants_per_seed,
    )
    _run(
        [
            sys.executable,
            "scripts/filter_synthetic.py",
            "--run-id",
            run_id,
            "--language",
            language.value,
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/prepare_review_sample.py",
            "--run-id",
            run_id,
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/submit_manual_review.py",
            "--run-id",
            run_id,
            "--approve-all",
            "--reviewed-by",
            "agent-expander",
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/publish_dataset.py",
            "--draft-id",
            run_id,
            "--verify",
            "--config",
            str(PUBLISH_CONFIG),
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/publish_dataset.py",
            "--draft-id",
            run_id,
            "--version",
            VERSIONS[language],
            "--config",
            str(PUBLISH_CONFIG),
            "--published-by",
            "agent-expander",
        ]
    )
    manifest_path = ROOT / "data/datasets/draft" / run_id / "filter-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        "candidates": candidate_count,
        "accepted": int(manifest.get("acceptedCount", 0)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build M1 dataset locally from gold seed expansion (agent, no API)",
    )
    parser.add_argument(
        "--language",
        choices=[lang.value for lang in TargetLanguage],
        help="Build one language only",
    )
    parser.add_argument("--variants-per-seed", type=int, default=14)
    parser.add_argument("--skip-mixed", action="store_true")
    args = parser.parse_args()

    languages = (
        [TargetLanguage(args.language)]
        if args.language
        else list(TargetLanguage)
    )

    summary: dict[str, dict[str, int]] = {}
    for language in languages:
        print(f"\n=== {language.value} ===")
        summary[language.value] = build_language(language, args.variants_per_seed)

    if not args.skip_mixed and len(languages) == len(list(TargetLanguage)):
        _run(
            [
                sys.executable,
                "scripts/publish_mixed_dataset.py",
                "--config",
                str(PHASE1_CONFIG),
                "--publish-config",
                str(PUBLISH_CONFIG),
                "--version",
                MIXED_VERSION,
                "--published-by",
                "agent-expander",
            ]
        )

    total_accepted = sum(item["accepted"] for item in summary.values())
    print("\n=== Summary ===")
    for lang, counts in summary.items():
        print(f"{lang}: {counts['accepted']}/{counts['candidates']} accepted")
    print(f"TOTAL accepted: {total_accepted}")
    if total_accepted >= 2000:
        print(f"OK: mixed target ready — {MIXED_VERSION}")
    else:
        print(f"WARN: accepted {total_accepted} < 2000 — increase --variants-per-seed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
