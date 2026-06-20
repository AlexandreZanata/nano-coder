"""Contract tests for Phase 4 evaluation workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase4_config_and_scripts_exist():
    config = yaml.safe_load((ROOT / "config" / "phase4-v1.yaml").read_text(encoding="utf-8"))
    assert config["defaults"]["heldOutTestSetVersion"] == "held-out-v1"
    assert config["evaluation"]["includeInferenceMetrics"] is True

    for script in ("run_phase4_evaluation.py", "show_evaluation_results.py"):
        assert (ROOT / "scripts" / script).is_file()
