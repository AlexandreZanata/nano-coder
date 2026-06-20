"""Phase 2 experiment configuration (exp_001 LoRA anchor)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule


@dataclass(frozen=True)
class Phase2Config:
    version: str
    experiment_id: str
    compression_method: CompressionMethod
    evidence_level: str
    wave: int
    dataset_version: str
    smoke_dataset_version: str
    student_model: str
    data_schedule: DataSchedule
    lora_rank: int
    held_out_test_set_version: str
    run_id_templates: dict[str, str]


def load_phase2_config(path: Path) -> Phase2Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    return Phase2Config(
        version=raw["version"],
        experiment_id=str(raw["experimentId"]),
        compression_method=CompressionMethod(raw["compressionMethod"]),
        evidence_level=str(raw["evidenceLevel"]),
        wave=int(raw["wave"]),
        dataset_version=str(defaults["datasetVersion"]),
        smoke_dataset_version=str(defaults["smokeDatasetVersion"]),
        student_model=str(defaults["studentModel"]),
        data_schedule=DataSchedule(defaults["dataSchedule"]),
        lora_rank=int(defaults["loraRank"]),
        held_out_test_set_version=str(defaults["heldOutTestSetVersion"]),
        run_id_templates=dict(raw["runIdTemplates"]),
    )


def format_run_id(template: str, *, profile: str) -> str:
    return template.format(profile=profile)
