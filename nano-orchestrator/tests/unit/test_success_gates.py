"""Unit tests for EG success-gate decision helpers."""

from __future__ import annotations

from nano_orchestrator.application.success_gates import (
    gate_001_orchestration_beats_solo,
    gate_002_vram_within_limit,
    gate_003_p50_within_target,
    overall_gates_pass,
)


def test_gate_001_pass_when_orch_ge_solo() -> None:
    v = gate_001_orchestration_beats_solo(orch_pass_at_1=0.7, solo_pass_at_1=0.6)
    assert v.passed is True


def test_gate_001_fail_when_orch_lt_solo() -> None:
    v = gate_001_orchestration_beats_solo(orch_pass_at_1=0.5, solo_pass_at_1=0.6)
    assert v.passed is False


def test_gate_001_tie_counts_as_pass() -> None:
    v = gate_001_orchestration_beats_solo(orch_pass_at_1=0.6, solo_pass_at_1=0.6)
    assert v.passed is True


def test_gate_002_vram() -> None:
    assert gate_002_vram_within_limit(peak_vram_mb=3547).passed is True
    assert gate_002_vram_within_limit(peak_vram_mb=6001).passed is False
    assert gate_002_vram_within_limit(peak_vram_mb=None).passed is False


def test_gate_003_p50() -> None:
    assert gate_003_p50_within_target(p50_ms=500, target_ms=2000).passed is True
    assert gate_003_p50_within_target(p50_ms=2500, target_ms=2000).passed is False


def test_overall_gates() -> None:
    ok = [
        gate_001_orchestration_beats_solo(orch_pass_at_1=0.8, solo_pass_at_1=0.7),
        gate_002_vram_within_limit(peak_vram_mb=3000),
        gate_003_p50_within_target(p50_ms=400),
    ]
    assert overall_gates_pass(ok) is True
    bad = ok + [gate_003_p50_within_target(p50_ms=9000)]
    # last fails
    assert overall_gates_pass(bad[:2] + [gate_003_p50_within_target(p50_ms=9000)]) is False
