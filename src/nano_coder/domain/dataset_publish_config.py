"""Dataset publish configuration (Stage 7, BR-005)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DatasetPublishConfig:
    version: str
    dataset_version_pattern: re.Pattern[str]
    min_accepted_per_language: int
    min_syntax_pass_rate: float
    require_manual_review: bool
    require_run_completed: bool
    examples_file: str
    manifest_file: str


def load_dataset_publish_config(path: Path) -> DatasetPublishConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    thresholds = raw["thresholds"]
    artifacts = raw["artifacts"]
    return DatasetPublishConfig(
        version=raw["version"],
        dataset_version_pattern=re.compile(raw["datasetVersionPattern"]),
        min_accepted_per_language=int(thresholds["minAcceptedPerLanguage"]),
        min_syntax_pass_rate=float(thresholds["minSyntaxPassRate"]),
        require_manual_review=bool(thresholds["requireManualReview"]),
        require_run_completed=bool(thresholds["requireRunCompleted"]),
        examples_file=str(artifacts["examplesFile"]),
        manifest_file=str(artifacts["manifestFile"]),
    )
