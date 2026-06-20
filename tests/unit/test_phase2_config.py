"""Unit tests for Phase 2 configuration."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.phase2_config import format_run_id, load_phase2_config

ROOT = Path(__file__).resolve().parents[2]


def test_load_phase2_config_reads_exp_001():
    config = load_phase2_config(ROOT / "config" / "phase2-v1.yaml")
    assert config.experiment_id == "exp_001_lora_baseline"
    assert config.compression_method is CompressionMethod.LORA
    assert config.lora_rank == 16


def test_format_run_id_substitutes_profile():
    run_id = format_run_id("train-lora-{profile}-001", profile="smoke")
    assert run_id == "train-lora-smoke-001"
