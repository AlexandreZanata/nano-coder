"""Unit tests for experiment configuration (Phase 3)."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.experiment_config import load_phase3_config

ROOT = Path(__file__).resolve().parents[2]


def test_load_phase3_config_wave1_experiments():
    config = load_phase3_config(ROOT / "config" / "phase3-v1.yaml")
    assert config.wave == 1
    assert "exp_002_qlora_baseline" in config.experiments
    qlora = config.experiments["exp_002_qlora_baseline"]
    assert qlora.compression_method is CompressionMethod.QLORA
    fewshot = config.experiments["fewshot_baseline"]
    assert fewshot.skip_train is True
