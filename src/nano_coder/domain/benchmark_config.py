"""Benchmark configuration (UC-004, EVALUATION-METHOD.md)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class BenchmarkConfig:
    version: str
    held_out_test_set_version: str
    pass_at_k: tuple[int, ...]
    samples_per_task: int
    mock_pass_ratio: float


def load_benchmark_config(path: Path) -> BenchmarkConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    return BenchmarkConfig(
        version=raw["version"],
        held_out_test_set_version=str(defaults["heldOutTestSetVersion"]),
        pass_at_k=tuple(int(item) for item in defaults["passAtK"]),
        samples_per_task=int(defaults["samplesPerTask"]),
        mock_pass_ratio=float(defaults["mockPassRatio"]),
    )
