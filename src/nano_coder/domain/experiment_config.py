"""Experiment specification for method comparison pipelines (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule


@dataclass(frozen=True)
class ExperimentSpec:
    experiment_id: str
    compression_method: CompressionMethod
    evidence_level: str
    method_slug: str
    dataset_version: str
    smoke_dataset_version: str
    student_model: str
    data_schedule: DataSchedule
    lora_rank: int
    held_out_test_set_version: str
    run_id_templates: dict[str, str]
    skip_train: bool = False


@dataclass(frozen=True)
class Phase3Config:
    version: str
    wave: int
    defaults: dict[str, str | int]
    experiments: dict[str, ExperimentSpec]
    ranking_primary_metric: str
    ranking_tie_breakers: tuple[str, ...]


def load_phase3_config(path: Path) -> Phase3Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    experiments: dict[str, ExperimentSpec] = {}
    for experiment_id, spec in raw["experiments"].items():
        experiments[experiment_id] = ExperimentSpec(
            experiment_id=experiment_id,
            compression_method=CompressionMethod(spec["compressionMethod"]),
            evidence_level=str(spec["evidenceLevel"]),
            method_slug=str(spec["methodSlug"]),
            dataset_version=str(defaults["datasetVersion"]),
            smoke_dataset_version=str(defaults["smokeDatasetVersion"]),
            student_model=str(defaults["studentModel"]),
            data_schedule=DataSchedule(defaults["dataSchedule"]),
            lora_rank=int(defaults["loraRank"]),
            held_out_test_set_version=str(defaults["heldOutTestSetVersion"]),
            run_id_templates=dict(spec["runIdTemplates"]),
            skip_train=bool(spec.get("skipTrain", False)),
        )
    ranking = raw.get("ranking", {})
    return Phase3Config(
        version=raw["version"],
        wave=int(raw["wave"]),
        defaults=defaults,
        experiments=experiments,
        ranking_primary_metric=str(ranking.get("primaryMetric", "passAt1")),
        ranking_tie_breakers=tuple(ranking.get("tieBreakers", [])),
    )


def format_run_id(template: str, *, profile: str) -> str:
    return template.format(profile=profile)
