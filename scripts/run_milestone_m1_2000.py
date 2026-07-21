#!/usr/bin/env python3
"""Milestone M1 — orchestrate 2,000-example pipeline (PLAN-2000-EXAMPLES.md)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from load_project_env import load_project_env  # noqa: E402

PHASE1_CONFIG = ROOT / ".local/overrides/phase1-milestone-2000.yaml"
PUBLISH_CONFIG = ROOT / ".local/overrides/dataset-publish-milestone-2000.yaml"
PROGRESS = ROOT / ".local/plans/PROGRESS-2000.yaml"

LANGUAGES = ("JavaScript", "HTML", "FreeMarker")
RUN_IDS = {
    "JavaScript": "gen-js-m2000-v2",
    "HTML": "gen-html-m2000-v2",
    "FreeMarker": "gen-fmt-m2000-v2",
}
VERSIONS = {
    "JavaScript": "ds-2026-06-21-js-m2000-v2",
    "HTML": "ds-2026-06-21-html-m2000-v2",
    "FreeMarker": "ds-2026-06-21-fmt-m2000-v2",
}
MIXED_VERSION = "ds-2026-06-21-mixed-m2000-v2"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=ROOT, check=check, text=True)


def phase0_readiness() -> None:
    _run(
        [
            sys.executable,
            "scripts/verify_phase1_readiness.py",
            "--config",
            str(PHASE1_CONFIG),
        ]
    )


def phase1_generate_filter(
    language: str,
    *,
    real: bool,
    target_count: int,
    max_batches: int | None,
) -> None:
    cmd = [
        sys.executable,
        "scripts/run_phase1_language.py",
        "--language",
        language,
        "--config",
        str(PHASE1_CONFIG),
        "--run-id",
        RUN_IDS[language],
        "--target-count",
        str(target_count),
        "--stop-after",
        "prepareReview",
    ]
    if max_batches is not None:
        cmd.extend(["--max-batches", str(max_batches)])
    if real:
        cmd.append("--real-generation")
    _run(cmd)

    manifest = ROOT / "data/datasets/draft" / RUN_IDS[language] / "filter-manifest.json"
    if manifest.is_file():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        print(
            f"Filter summary {language}: "
            f"{data.get('acceptedCount')}/{data.get('candidateCount')} accepted, "
            f"syntaxPassRate={data.get('syntaxPassRate')}"
        )


def phase3_publish(language: str) -> None:
    run_id = RUN_IDS[language]
    version = VERSIONS[language]
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
            version,
            "--config",
            str(PUBLISH_CONFIG),
            "--published-by",
            "pipeline-operator",
        ]
    )


def phase3_publish_mixed() -> None:
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
        ]
    )


def phase5_experiments(profile: str, real: bool) -> None:
    for exp in (
        "experiments/exp_001_lora_baseline/run.py",
        "experiments/exp_002_qlora_baseline/run.py",
    ):
        cmd = [
            sys.executable,
            exp,
            "--profile",
            profile,
            "--dataset-version",
            MIXED_VERSION,
        ]
        if real:
            cmd.append("--real")
        _run(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run M1 2,000-example milestone pipeline")
    parser.add_argument(
        "--phase",
        type=int,
        choices=(0, 1, 3, 5),
        required=True,
        help="0=readiness, 1=generate+filter+review-prep, 3=publish, 5=exp_001+exp_002",
    )
    parser.add_argument("--language", choices=LANGUAGES, help="Required for phase 1 and 3")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use teacher API (requires TEACHER_API_KEY in .env)",
    )
    parser.add_argument("--target-count", type=int, default=1100)
    parser.add_argument("--max-batches", type=int, help="Limit batches (smoke / dry-run)")
    parser.add_argument("--profile", default="publication", choices=("ci", "smoke", "publication"))
    args = parser.parse_args()

    load_project_env(ROOT)

    if args.real and not __import__("os").environ.get("TEACHER_API_KEY", "").strip():
        print(
            "ERROR: TEACHER_API_KEY is required for --real generation.\n"
            "Copy .env.example to .env and set TEACHER_API_KEY=your-key",
            file=sys.stderr,
        )
        return 1

    if args.phase == 0:
        phase0_readiness()
        return 0

    if args.phase == 1:
        if not args.language:
            print("ERROR: --language required for phase 1", file=sys.stderr)
            return 1
        phase1_generate_filter(
            args.language,
            real=args.real,
            target_count=args.target_count,
            max_batches=args.max_batches,
        )
        print(
            f"\nNext: manual review — "
            f".local/review/{RUN_IDS[args.language]}/review-queue.json\n"
            f"Then: python3 scripts/submit_manual_review.py --run-id {RUN_IDS[args.language]}"
        )
        return 0

    if args.phase == 3:
        if args.language:
            phase3_publish(args.language)
        else:
            for lang in LANGUAGES:
                phase3_publish(lang)
            phase3_publish_mixed()
        return 0

    if args.phase == 5:
        phase5_experiments(args.profile, real=args.real)
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
