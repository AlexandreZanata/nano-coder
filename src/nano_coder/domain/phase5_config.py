"""Phase 5 reporting configuration (UC-005, Part 5 operator playbook)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Phase5Config:
    version: str
    wave: int
    profile: str
    output_markdown: str
    output_json: str
    primary_metric: str
    tie_breakers: tuple[str, ...]
    languages: tuple[str, ...]
    phase4_report: str
    phase3_report: str
    param_match_tolerance_percent: float
    label_speculative_as_non_comparable: bool


def load_phase5_config(path: Path) -> Phase5Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    ranking = raw["ranking"]
    sources = raw["sources"]
    footnotes = raw["footnotes"]
    return Phase5Config(
        version=raw["version"],
        wave=int(raw["wave"]),
        profile=str(defaults["profile"]),
        output_markdown=str(defaults["outputMarkdown"]),
        output_json=str(defaults["outputJson"]),
        primary_metric=str(ranking["primaryMetric"]),
        tie_breakers=tuple(ranking["tieBreakers"]),
        languages=tuple(ranking["languages"]),
        phase4_report=str(sources["phase4Report"]),
        phase3_report=str(sources["phase3Report"]),
        param_match_tolerance_percent=float(footnotes["paramMatchTolerancePercent"]),
        label_speculative_as_non_comparable=bool(footnotes["labelSpeculativeAsNonComparable"]),
    )
