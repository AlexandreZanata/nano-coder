#!/usr/bin/env python3
"""Shared stub for benchmark experiments until training stack is implemented."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "logs" / "experiments.jsonl"


def append_log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_stub(
    experiment_id: str,
    compression_method: str,
    evidence_level: str,
    profile: str,
    **extra,
) -> int:
    append_log(
        {
            "experiment_id": experiment_id,
            "compression_method": compression_method,
            "evidence_level": evidence_level,
            "profile": profile,
            "status": "stub",
            "message": "Training stack not implemented — CI wiring only",
            **extra,
        }
    )
    print(f"OK: {experiment_id} stub logged (profile={profile})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="ci", choices=["ci", "smoke", "publication"])
    args = parser.parse_args(argv)
    return run_stub("unknown", "Unknown", "Established", args.profile)


if __name__ == "__main__":
    raise SystemExit(main())
