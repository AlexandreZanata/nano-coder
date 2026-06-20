"""Contract tests for Stage 7 dataset publish workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_dataset_publish_config_exists():
    path = ROOT / "config" / "dataset-publish-v1.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["version"] == "v1"
    assert raw["thresholds"]["minAcceptedPerLanguage"] == 1500


def test_publish_dataset_script_exists():
    assert (ROOT / "scripts" / "publish_dataset.py").is_file()
