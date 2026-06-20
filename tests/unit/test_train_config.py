"""Unit tests for train configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.train_config import (
    TrainConfigError,
    load_train_config,
    resolve_train_profile,
    validate_train_hyperparams,
)

ROOT = Path(__file__).resolve().parents[2]


def test_load_train_config_reads_profiles():
    config = load_train_config(ROOT / "config" / "train-v1.yaml")
    assert config.default_profile == "smoke"
    smoke = resolve_train_profile(config, "smoke")
    assert smoke.max_train_examples == 200
    assert smoke.max_steps == 100


def test_validate_train_hyperparams_requires_lora_rank():
    with pytest.raises(TrainConfigError):
        validate_train_hyperparams(compression_method=CompressionMethod.LORA, lora_rank=None)
