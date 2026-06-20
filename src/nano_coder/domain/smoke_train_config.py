"""Smoke train configuration (Stage 8, ADR-002)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.compression_method import CompressionMethod


@dataclass(frozen=True)
class SmokeTrainConfig:
    version: str
    profile: str
    student_model: str
    compression_method: CompressionMethod
    lora_rank: int
    max_train_examples: int
    epochs: int
    batch_size: int
    learning_rate: float
    smoke_eval_tasks: int
    min_pass_at_1: float
    random_seed: int
    iteration_hints: tuple[str, ...]


def load_smoke_train_config(path: Path) -> SmokeTrainConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    return SmokeTrainConfig(
        version=raw["version"],
        profile=raw["profile"],
        student_model=str(defaults["studentModel"]),
        compression_method=CompressionMethod(defaults["compressionMethod"]),
        lora_rank=int(defaults["loraRank"]),
        max_train_examples=int(defaults["maxTrainExamples"]),
        epochs=int(defaults["epochs"]),
        batch_size=int(defaults["batchSize"]),
        learning_rate=float(defaults["learningRate"]),
        smoke_eval_tasks=int(defaults["smokeEvalTasks"]),
        min_pass_at_1=float(defaults["minPassAt1"]),
        random_seed=int(defaults["randomSeed"]),
        iteration_hints=tuple(str(item) for item in raw["iterationHints"]),
    )
