"""Phase 4 evaluation readiness checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from nano_coder.domain.benchmark_eval import load_held_out_manifest, validate_test_set_version


@dataclass(frozen=True)
class EvaluationReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class EvaluationReadinessResult:
    passed: bool
    checks: tuple[EvaluationReadinessCheck, ...]


def verify_evaluation_readiness(
    *,
    held_out_root: Path,
    benchmark_root: Path,
    benchmark_run_ids: list[str],
    expected_test_set_version: str,
) -> EvaluationReadinessResult:
    checks: list[EvaluationReadinessCheck] = []

    try:
        manifest = validate_test_set_version(
            held_out_root,
            expected_version=expected_test_set_version,
        )
        checks.append(
            EvaluationReadinessCheck(
                name="held-out-v1",
                passed=True,
                detail=f"{manifest.get('taskCount', 0)} tasks immutable",
            )
        )
    except Exception as exc:
        checks.append(
            EvaluationReadinessCheck(
                name="held-out-v1",
                passed=False,
                detail=str(exc),
            )
        )

    if held_out_root.joinpath("manifest.json").is_file():
        raw = json.loads(held_out_root.joinpath("manifest.json").read_text(encoding="utf-8"))
        if raw.get("immutable") is True:
            checks.append(
                EvaluationReadinessCheck(
                    name="BR-004 isolation",
                    passed=True,
                    detail="held-out test set marked immutable",
                )
            )

    for run_id in benchmark_run_ids:
        results_path = benchmark_root / run_id / "results.json"
        if results_path.is_file():
            checks.append(
                EvaluationReadinessCheck(
                    name=f"benchmark {run_id}",
                    passed=True,
                    detail=str(results_path),
                )
            )
        else:
            checks.append(
                EvaluationReadinessCheck(
                    name=f"benchmark {run_id}",
                    passed=False,
                    detail="results.json missing",
                )
            )

    return EvaluationReadinessResult(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )


def load_held_out_task_count(held_out_root: Path) -> int:
    manifest = load_held_out_manifest(held_out_root)
    return int(manifest.get("taskCount", 0))
