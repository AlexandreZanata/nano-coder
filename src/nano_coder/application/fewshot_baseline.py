"""FewShot baseline — no weight update (UC-004 AF-2, Phase 3 Wave 1)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule


@dataclass(frozen=True)
class FewShotBaselineResult:
    run_id: str
    checkpoint_dir: Path
    manifest_path: Path


def run_fewshot_baseline(
    *,
    run_id: str,
    dataset_version: str,
    student_model: str,
    data_schedule: DataSchedule,
    checkpoint_root: Path,
    profile: str,
    evidence_level: str = "Established",
    events_log: Path | None = None,
) -> FewShotBaselineResult:
    checkpoint_dir = checkpoint_root / run_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "runId": run_id,
        "datasetVersion": dataset_version,
        "studentModel": student_model,
        "compressionMethod": CompressionMethod.FEW_SHOT.value,
        "dataSchedule": data_schedule.value,
        "profile": profile,
        "trainExampleCount": 0,
        "steps": 0,
        "seed": None,
        "trainableParamCount": 0,
        "peakVramGb": 0.0,
        "durationSeconds": 0.0,
        "evidenceLevel": evidence_level,
        "heldOutTestSetVersion": "held-out-v1",
        "backend": "fewshot-baseline",
        "dryRun": True,
        "completedAt": datetime.now(UTC).isoformat(),
    }
    manifest_path = checkpoint_dir / "checkpoint-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _append_event(
        events_log,
        {
            "event": "FewShotBaselineRegistered",
            "runId": run_id,
            "datasetVersion": dataset_version,
        },
    )

    return FewShotBaselineResult(
        run_id=run_id,
        checkpoint_dir=checkpoint_dir,
        manifest_path=manifest_path,
    )


def _append_event(path: Path | None, event: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("timestamp", datetime.now(UTC).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
