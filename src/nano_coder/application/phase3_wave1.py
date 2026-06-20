"""Application service — Wave 1 method comparison orchestrator (Phase 3)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from nano_coder.application.method_experiment_pipeline import (
    MethodExperimentResult,
    run_method_experiment,
)
from nano_coder.domain.experiment_config import Phase3Config, load_phase3_config


@dataclass
class Phase3WaveResult:
    wave: int
    profile: str
    dataset_version: str
    failed: bool = False
    experiments: list[MethodExperimentResult] = field(default_factory=list)


def run_phase3_wave1(
    *,
    config: Phase3Config,
    project_root: Path,
    profile: str = "smoke",
    dataset_version: str | None = None,
    experiment_ids: list[str] | None = None,
    run_smoke: bool = False,
) -> Phase3WaveResult:
    version = dataset_version or str(config.defaults["datasetVersion"])
    selected = experiment_ids or list(config.experiments.keys())
    wave_result = Phase3WaveResult(wave=config.wave, profile=profile, dataset_version=version)

    for experiment_id in selected:
        if experiment_id not in config.experiments:
            wave_result.failed = True
            continue
        spec = config.experiments[experiment_id]
        result = run_method_experiment(
            spec=spec,
            project_root=project_root,
            profile=profile,
            dataset_version=version,
            run_smoke=run_smoke,
        )
        wave_result.experiments.append(result)
        if result.failed:
            wave_result.failed = True

    _write_wave_report(wave_result, project_root)
    return wave_result


def _write_wave_report(result: Phase3WaveResult, project_root: Path) -> None:
    report_path = project_root / ".local" / "review" / "phase3-wave1-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "wave": result.wave,
        "profile": result.profile,
        "datasetVersion": result.dataset_version,
        "failed": result.failed,
        "completedAt": datetime.now(UTC).isoformat(),
        "experiments": [
            {
                "experimentId": experiment.experiment_id,
                "compressionMethod": experiment.compression_method,
                "failed": experiment.failed,
                "trainRunId": experiment.train_run_id,
                "benchmarkRunId": experiment.benchmark_run_id,
            }
            for experiment in result.experiments
        ],
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_phase3_wave_config(path: Path) -> Phase3Config:
    return load_phase3_config(path)
