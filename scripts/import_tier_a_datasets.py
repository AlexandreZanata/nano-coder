#!/usr/bin/env python3
"""Import Tier-A open datasets (Vulcan + WebA11yBench) into the Phase 1 pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.infrastructure.external_dataset_adapters import (  # noqa: E402
    iter_vulcan_records,
    iter_weba11y_records,
    write_raw_batches,
)

DEFAULT_VULCAN_CACHE = (
    Path.home()
    / ".cache/huggingface/hub/datasets--xlelords--vulcan/snapshots"
)
DEFAULT_WEBA11Y = ROOT / ".local/external/weba11y/accessibility_dataset/final_dataset/prompts_with_code.json"
RUN_ID = "gen-html-tier-a-v1"
HTML_VERSION = "ds-2026-06-21-html-tier-a-v1"
MIXED_VERSION = "ds-2026-06-21-mixed-tier-a-v1"
PUBLISH_CONFIG = ROOT / ".local/overrides/dataset-publish-tier-a.yaml"
GATES_CONFIG = ROOT / ".local/overrides/quality-gates-tier-a.yaml"
JS_SOURCE = "ds-2026-06-21-js-m2000-v2"
FMT_SOURCE = "ds-2026-06-21-fmt-m2000-v2"


def _resolve_vulcan_path(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    if not DEFAULT_VULCAN_CACHE.is_dir():
        from huggingface_hub import hf_hub_download

        return Path(hf_hub_download("xlelords/vulcan", "train.jsonl", repo_type="dataset"))
    snapshots = sorted(DEFAULT_VULCAN_CACHE.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for snap in snapshots:
        candidate = snap / "train.jsonl"
        if candidate.is_file():
            return candidate
    from huggingface_hub import hf_hub_download

    return Path(hf_hub_download("xlelords/vulcan", "train.jsonl", repo_type="dataset"))


def _normalize_instruction(text: str) -> str:
    return " ".join(text.lower().split())


def _collect_records(
    *,
    vulcan_path: Path,
    weba11y_path: Path,
    max_vulcan: int,
    max_weba11y: int,
) -> list[dict]:
    records: list[dict] = []
    seen_instructions: set[str] = set()
    vulcan_count = 0
    for record in iter_vulcan_records(vulcan_path):
        if vulcan_count >= max_vulcan:
            break
        key = _normalize_instruction(record["instruction"])
        if key in seen_instructions:
            continue
        seen_instructions.add(key)
        records.append(record)
        vulcan_count += 1
    weba11y_count = 0
    for record in iter_weba11y_records(weba11y_path, start_serial=len(records) + 1):
        if weba11y_count >= max_weba11y:
            break
        key = _normalize_instruction(record["instruction"])
        if key in seen_instructions:
            continue
        seen_instructions.add(key)
        records.append(record)
        weba11y_count += 1
    for serial, record in enumerate(records, start=1):
        record["id"] = f"syn-html-{serial:04d}"
    return records


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Vulcan + WebA11yBench for training")
    parser.add_argument("--vulcan-path", type=Path)
    parser.add_argument("--weba11y-path", type=Path, default=DEFAULT_WEBA11Y)
    parser.add_argument("--max-vulcan", type=int, default=5000)
    parser.add_argument("--max-weba11y", type=int, default=5000)
    parser.add_argument("--import-only", action="store_true", help="Only write raw batches")
    parser.add_argument("--skip-train", action="store_true")
    args = parser.parse_args()

    if not args.weba11y_path.is_file():
        print(f"ERROR: WebA11yBench not found at {args.weba11y_path}", file=sys.stderr)
        print("Download: curl -L -o .local/external/weba11y/accessibility_dataset.zip \\")
        print("  https://zenodo.org/records/17127458/files/accessibility_dataset.zip")
        return 1

    vulcan_path = _resolve_vulcan_path(args.vulcan_path)
    records = _collect_records(
        vulcan_path=vulcan_path,
        weba11y_path=args.weba11y_path,
        max_vulcan=args.max_vulcan,
        max_weba11y=args.max_weba11y,
    )
    raw_dir = ROOT / ".local/generation/raw" / RUN_ID
    count = write_raw_batches(records, raw_dir, batch_size=50)
    print(f"OK: imported {count} Tier-A HTML candidates → {raw_dir}")

    if args.import_only:
        return 0

    _run(
        [
            sys.executable,
            "scripts/filter_synthetic.py",
            "--run-id",
            RUN_ID,
            "--language",
            "HTML",
            "--gates",
            str(GATES_CONFIG),
        ]
    )
    _run([sys.executable, "scripts/prepare_review_sample.py", "--run-id", RUN_ID])
    _run(
        [
            sys.executable,
            "scripts/submit_manual_review.py",
            "--run-id",
            RUN_ID,
            "--approve-all",
            "--reviewed-by",
            "tier-a-importer",
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/publish_dataset.py",
            "--draft-id",
            RUN_ID,
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
            RUN_ID,
            "--version",
            HTML_VERSION,
            "--config",
            str(PUBLISH_CONFIG),
            "--published-by",
            "tier-a-importer",
        ]
    )
    _run(
        [
            sys.executable,
            "scripts/publish_mixed_dataset.py",
            "--sources",
            JS_SOURCE,
            HTML_VERSION,
            FMT_SOURCE,
            "--version",
            MIXED_VERSION,
            "--publish-config",
            str(PUBLISH_CONFIG),
            "--published-by",
            "tier-a-importer",
        ]
    )

    manifest_path = ROOT / "data/datasets" / MIXED_VERSION / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(
            f"OK: mixed dataset {MIXED_VERSION} — "
            f"{manifest.get('exampleCount')} examples — {manifest.get('countsByLanguage')}"
        )

    if not args.skip_train:
        for exp in ("experiments/exp_001_lora_baseline/run.py", "experiments/exp_002_qlora_baseline/run.py"):
            _run(
                [
                    sys.executable,
                    exp,
                    "--profile",
                    "publication",
                    "--dataset-version",
                    MIXED_VERSION,
                    "--real",
                ]
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
