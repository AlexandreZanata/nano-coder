"""Success-gate decision helpers (GATE-001…003) — pure, no I/O."""

from __future__ import annotations

from dataclasses import dataclass


# README §0 / Phase 1 reference (T-023): simple micro-task p50 target.
DEFAULT_P50_TARGET_MS = 2000
DEFAULT_VRAM_LIMIT_MB = 6000


@dataclass(frozen=True, slots=True)
class GateVerdict:
    gate_id: str
    passed: bool
    metric: float
    threshold: float
    detail: str


def gate_001_orchestration_beats_solo(
    *,
    orch_pass_at_1: float,
    solo_pass_at_1: float,
) -> GateVerdict:
    passed = orch_pass_at_1 >= solo_pass_at_1
    return GateVerdict(
        gate_id="GATE-001",
        passed=passed,
        metric=orch_pass_at_1,
        threshold=solo_pass_at_1,
        detail=(
            f"orch Pass@1={orch_pass_at_1:.4f} "
            f"{'≥' if passed else '<'} solo Pass@1={solo_pass_at_1:.4f}"
        ),
    )


def gate_002_vram_within_limit(
    *,
    peak_vram_mb: float | None,
    limit_mb: float = DEFAULT_VRAM_LIMIT_MB,
) -> GateVerdict:
    if peak_vram_mb is None:
        return GateVerdict(
            gate_id="GATE-002",
            passed=False,
            metric=-1.0,
            threshold=limit_mb,
            detail="peak VRAM unavailable (nvidia-smi)",
        )
    passed = peak_vram_mb <= limit_mb
    return GateVerdict(
        gate_id="GATE-002",
        passed=passed,
        metric=float(peak_vram_mb),
        threshold=limit_mb,
        detail=f"peak VRAM={peak_vram_mb:.0f} MB {'≤' if passed else '>'} {limit_mb:.0f} MB",
    )


def gate_003_p50_within_target(
    *,
    p50_ms: float | None,
    target_ms: float = DEFAULT_P50_TARGET_MS,
) -> GateVerdict:
    if p50_ms is None:
        return GateVerdict(
            gate_id="GATE-003",
            passed=False,
            metric=-1.0,
            threshold=target_ms,
            detail="p50 latency unavailable",
        )
    passed = p50_ms <= target_ms
    return GateVerdict(
        gate_id="GATE-003",
        passed=passed,
        metric=float(p50_ms),
        threshold=target_ms,
        detail=f"p50={p50_ms:.0f} ms {'≤' if passed else '>'} target {target_ms:.0f} ms",
    )


def overall_gates_pass(verdicts: list[GateVerdict]) -> bool:
    return all(v.passed for v in verdicts)
