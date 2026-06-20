"""Contract tests for Phase 2 LoRA anchor workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_phase2_configs_and_scripts_exist():
    train_cfg = yaml.safe_load((ROOT / "config" / "train-v1.yaml").read_text(encoding="utf-8"))
    bench_cfg = yaml.safe_load((ROOT / "config" / "benchmark-v1.yaml").read_text(encoding="utf-8"))
    phase2_cfg = yaml.safe_load((ROOT / "config" / "phase2-v1.yaml").read_text(encoding="utf-8"))

    assert train_cfg["version"] == "v1"
    assert bench_cfg["defaults"]["heldOutTestSetVersion"] == "held-out-v1"
    assert phase2_cfg["experimentId"] == "exp_001_lora_baseline"

    for script in ("train.py", "benchmark.py", "run_phase2_lora.py"):
        assert (ROOT / "scripts" / script).is_file()

    assert (ROOT / "src" / "nano_coder" / "cli" / "main.py").is_file()
