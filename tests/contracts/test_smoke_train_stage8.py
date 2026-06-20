"""Contract tests for Stage 8 smoke train workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_smoke_train_config_exists():
    path = ROOT / "config" / "smoke-train-v1.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["profile"] == "smoke"
    assert raw["defaults"]["minPassAt1"] == 0.60


def test_smoke_train_script_exists():
    assert (ROOT / "scripts" / "smoke_train.py").is_file()
