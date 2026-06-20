"""Contract tests for Stage 6 manual review workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_manual_review_config_exists():
    path = ROOT / "config" / "manual-review-v1.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["version"] == "v1"
    assert raw["sampleRate"] == 0.05


def test_manual_review_scripts_exist():
    assert (ROOT / "scripts" / "prepare_review_sample.py").is_file()
    assert (ROOT / "scripts" / "submit_manual_review.py").is_file()
