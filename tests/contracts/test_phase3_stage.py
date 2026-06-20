"""Contract tests for Phase 3 Wave 1 method comparison."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase3_config_and_scripts_exist():
    config = yaml.safe_load((ROOT / "config" / "phase3-v1.yaml").read_text(encoding="utf-8"))
    assert config["wave"] == 1
    assert "exp_002_qlora_baseline" in config["experiments"]
    assert "fewshot_baseline" in config["experiments"]

    for script in ("run_phase3_wave1.py", "report_export.py"):
        assert (ROOT / "scripts" / script).is_file()
