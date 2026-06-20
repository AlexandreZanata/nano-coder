"""Unit tests for Phase 5 configuration."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.phase5_config import load_phase5_config

ROOT = Path(__file__).resolve().parents[2]


def test_load_phase5_config_reads_ranking_defaults():
    config = load_phase5_config(ROOT / "config" / "phase5-v1.yaml")
    assert config.wave == 1
    assert config.languages == ("JavaScript", "HTML", "FreeMarker")
    assert config.primary_metric == "passAt1"
