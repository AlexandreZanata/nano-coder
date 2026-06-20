"""Contract tests for Phase 1 operator workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase1_config_and_scripts_exist():
    config = yaml.safe_load((ROOT / "config" / "phase1-v1.yaml").read_text(encoding="utf-8"))
    assert config["version"] == "v1"
    assert config["requiredSeedsPerLanguage"] == 50
    for script in (
        "run_phase1_language.py",
        "publish_mixed_dataset.py",
        "verify_phase1_readiness.py",
    ):
        assert (ROOT / "scripts" / script).is_file()
