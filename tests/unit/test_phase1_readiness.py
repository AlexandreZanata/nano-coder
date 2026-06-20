"""Unit tests for Phase 1 readiness checks."""

from __future__ import annotations

from pathlib import Path

from nano_coder.domain.phase1_config import load_phase1_config
from nano_coder.domain.phase1_readiness import verify_phase1_readiness

ROOT = Path(__file__).resolve().parents[2]


def test_verify_phase1_readiness_passes_for_promoted_seeds():
    config = load_phase1_config(ROOT / "config" / "phase1-v1.yaml")
    result = verify_phase1_readiness(
        seeds_root=ROOT / "data" / "seeds",
        published_root=ROOT / "data" / "datasets",
        config=config,
    )
    seed_checks = [check for check in result.checks if check.name.startswith("BR-001")]
    assert all(check.passed for check in seed_checks)
