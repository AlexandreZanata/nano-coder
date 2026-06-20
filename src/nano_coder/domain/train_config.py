"""Training configuration (UC-003, Phase 2 LoRA anchor)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule


class TrainConfigError(Exception):
    """Invalid training configuration."""


_LORA_METHODS = frozenset(
    {
        CompressionMethod.LORA,
        CompressionMethod.QLORA,
        CompressionMethod.DORA,
    }
)


@dataclass(frozen=True)
class TrainProfile:
    max_steps: int
    max_train_examples: int
    seeds: tuple[int, ...]


@dataclass(frozen=True)
class TrainConfig:
    version: str
    default_profile: str
    student_model: str
    data_schedule: DataSchedule
    compression_method: CompressionMethod
    lora_rank: int
    batch_size: int
    learning_rate: float
    epochs: int
    profiles: dict[str, TrainProfile]


def load_train_config(path: Path) -> TrainConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    profiles: dict[str, TrainProfile] = {}
    for name, profile in raw["profiles"].items():
        profiles[name] = TrainProfile(
            max_steps=int(profile["maxSteps"]),
            max_train_examples=int(profile["maxTrainExamples"]),
            seeds=tuple(int(seed) for seed in profile["seeds"]),
        )
    return TrainConfig(
        version=raw["version"],
        default_profile=str(raw["defaultProfile"]),
        student_model=str(defaults["studentModel"]),
        data_schedule=DataSchedule(defaults["dataSchedule"]),
        compression_method=CompressionMethod(defaults["compressionMethod"]),
        lora_rank=int(defaults["loraRank"]),
        batch_size=int(defaults["batchSize"]),
        learning_rate=float(defaults["learningRate"]),
        epochs=int(defaults["epochs"]),
        profiles=profiles,
    )


def resolve_train_profile(config: TrainConfig, profile: str) -> TrainProfile:
    if profile not in config.profiles:
        raise TrainConfigError(f"unknown training profile: {profile}")
    return config.profiles[profile]


def validate_train_hyperparams(
    *,
    compression_method: CompressionMethod,
    lora_rank: int | None,
) -> None:
    if compression_method in _LORA_METHODS and lora_rank is None:
        raise TrainConfigError(f"lora-rank required for {compression_method.value}")
