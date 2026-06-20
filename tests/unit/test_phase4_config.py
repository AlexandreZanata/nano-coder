"""Unit tests for Phase 4 configuration."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.phase4_config import load_phase4_config

ROOT = Path(__file__).resolve().parents[2]


def test_load_phase4_config_reads_evaluation_settings():
    config = load_phase4_config(ROOT / "config" / "phase4-v1.yaml")
    assert config.held_out_test_set_version == "held-out-v1"
    assert config.evaluation.include_tag_buckets is True
    assert config.anchor_compression_method == "LoRA"
