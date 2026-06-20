"""Unit tests for Phase 1 configuration."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.phase1_config import (
    format_dataset_version,
    format_mixed_version,
    format_run_id,
    load_phase1_config,
)
from nano_coder.domain.target_language import TargetLanguage

ROOT = Path(__file__).resolve().parents[2]


def test_phase1_config_formats_run_and_version_ids():
    config = load_phase1_config(ROOT / "config" / "phase1-v1.yaml")
    assert format_run_id(config, TargetLanguage.JAVASCRIPT) == "gen-js-v1"
    assert format_dataset_version(config, TargetLanguage.HTML) == "ds-2026-06-20-html-v1"
    assert format_mixed_version(config) == "ds-2026-06-20-mixed-v1"
