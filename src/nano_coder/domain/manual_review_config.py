"""Manual review configuration (Stage 6, BR-005)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ManualReviewConfig:
    version: str
    sample_rate: float
    min_sample_size: int
    require_all_sample_accepted: bool
    review_criteria: tuple[str, ...]


def load_manual_review_config(path: Path) -> ManualReviewConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ManualReviewConfig(
        version=raw["version"],
        sample_rate=float(raw["sampleRate"]),
        min_sample_size=int(raw["minSampleSize"]),
        require_all_sample_accepted=bool(raw["requireAllSampleAccepted"]),
        review_criteria=tuple(str(item) for item in raw["reviewCriteria"]),
    )
