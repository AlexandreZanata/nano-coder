"""Contract tests for Phase 5 reporting workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase5_config_and_script_exist():
    config = yaml.safe_load((ROOT / "config" / "phase5-v1.yaml").read_text(encoding="utf-8"))
    assert config["wave"] == 1
    assert "JavaScript" in config["ranking"]["languages"]
    assert (ROOT / "scripts" / "run_phase5_ranking.py").is_file()
