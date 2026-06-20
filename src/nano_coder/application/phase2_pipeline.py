"""Application service — Phase 2 LoRA anchor pipeline (Part 2 operator playbook)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from nano_coder.application.benchmark import run_benchmark
from nano_coder.application.smoke_train import run_smoke_train
from nano_coder.application.train import run_train
from nano_coder.domain.benchmark_config import BenchmarkConfig, load_benchmark_config
from nano_coder.domain.phase2_config import Phase2Config, format_run_id
from nano_coder.domain.smoke_train_config import SmokeTrainConfig, load_smoke_train_config
from nano_coder.domain.train_config import TrainConfig, load_train_config
from nano_coder.domain.training_run import TrainingRunState


class Phase2Step(StrEnum):
    SMOKE_TRAIN = "smokeTrain"
    TRAIN = "train"
    BENCHMARK = "benchmark"


@dataclass(frozen=True)
class Phase2StepResult:
    step: Phase2Step
    success: bool
    message: str


@dataclass
class Phase2PipelineResult:
    experiment_id: str
    profile: str
    dataset_version: str
    train_run_id: str
    benchmark_run_id: str
    failed: bool = False
    steps: list[Phase2StepResult] = field(default_factory=list)

    def record(self, step: Phase2Step, success: bool, message: str) -> None:
        self.steps.append(Phase2StepResult(step=step, success=success, message=message))
        if not success:
            self.failed = True


def run_phase2_lora_pipeline(
    *,
    config: Phase2Config,
    project_root: Path,
    profile: str = "smoke",
    dataset_version: str | None = None,
    train_run_id: str | None = None,
    benchmark_run_id: str | None = None,
    run_smoke: bool = False,
    stop_after: Phase2Step | None = None,
) -> Phase2PipelineResult:
    paths = _resolve_paths(project_root)
    version = dataset_version or config.dataset_version
    smoke_run_id = format_run_id(config.run_id_templates["smokeTrain"], profile=profile)
    resolved_train_id = train_run_id or format_run_id(
        config.run_id_templates["train"],
        profile=profile,
    )
    resolved_bench_id = benchmark_run_id or format_run_id(
        config.run_id_templates["benchmark"],
        profile=profile,
    )

    result = Phase2PipelineResult(
        experiment_id=config.experiment_id,
        profile=profile,
        dataset_version=version,
        train_run_id=resolved_train_id,
        benchmark_run_id=resolved_bench_id,
    )

    train_cfg = load_train_config(paths["train_config"])
    bench_cfg = load_benchmark_config(paths["benchmark_config"])
    smoke_cfg = load_smoke_train_config(paths["smoke_config"])

    if run_smoke:
        _step_smoke_train(
            result,
            run_id=smoke_run_id,
            dataset_version=config.smoke_dataset_version,
            smoke_cfg=smoke_cfg,
            paths=paths,
        )
        if result.failed or stop_after is Phase2Step.SMOKE_TRAIN:
            return _finalize(result, paths)

    _step_train(
        result,
        run_id=resolved_train_id,
        dataset_version=version,
        config=config,
        train_cfg=train_cfg,
        profile=profile,
        paths=paths,
    )
    if result.failed or stop_after is Phase2Step.TRAIN:
        return _finalize(result, paths)

    _step_benchmark(
        result,
        run_id=resolved_bench_id,
        train_run_id=resolved_train_id,
        bench_cfg=bench_cfg,
        paths=paths,
    )
    return _finalize(result, paths)


def _step_smoke_train(
    result: Phase2PipelineResult,
    *,
    run_id: str,
    dataset_version: str,
    smoke_cfg: SmokeTrainConfig,
    paths: dict[str, Path],
) -> None:
    try:
        smoke = run_smoke_train(
            run_id=run_id,
            dataset_version=dataset_version,
            published_root=paths["published"],
            held_out_root=paths["held_out"],
            checkpoint_root=paths["checkpoints"],
            output_root=paths["smoke_output"],
            config=smoke_cfg,
            dry_run=True,
        )
        gate = "pass" if smoke.eval_summary.gate_satisfied else "fail"
        result.record(
            Phase2Step.SMOKE_TRAIN,
            smoke.training_state is TrainingRunState.COMPLETED,
            f"Pass@1 {smoke.eval_summary.pass_at_1:.1%} gate={gate}",
        )
    except Exception as exc:
        result.record(Phase2Step.SMOKE_TRAIN, False, str(exc))


def _step_train(
    result: Phase2PipelineResult,
    *,
    run_id: str,
    dataset_version: str,
    config: Phase2Config,
    train_cfg: TrainConfig,
    profile: str,
    paths: dict[str, Path],
) -> None:
    try:
        train = run_train(
            run_id=run_id,
            dataset_version=dataset_version,
            compression_method=config.compression_method,
            student_model=config.student_model,
            data_schedule=config.data_schedule,
            published_root=paths["published"],
            checkpoint_root=paths["checkpoints"],
            config=train_cfg,
            profile=profile,
            lora_rank=config.lora_rank,
            events_log=paths["events"],
            dry_run=True,
        )
        result.record(
            Phase2Step.TRAIN,
            train.training_state is TrainingRunState.COMPLETED,
            f"trained {train.train_example_count} examples → {train.checkpoint_dir.name}",
        )
    except Exception as exc:
        result.record(Phase2Step.TRAIN, False, str(exc))


def _step_benchmark(
    result: Phase2PipelineResult,
    *,
    run_id: str,
    train_run_id: str,
    bench_cfg: BenchmarkConfig,
    paths: dict[str, Path],
) -> None:
    try:
        bench = run_benchmark(
            run_id=run_id,
            checkpoint_dir=paths["checkpoints"] / train_run_id,
            held_out_root=paths["held_out"],
            output_root=paths["benchmark_output"],
            config=bench_cfg,
            test_set_version=bench_cfg.held_out_test_set_version,
            events_log=paths["events"],
            dry_run=True,
        )
        result.record(
            Phase2Step.BENCHMARK,
            True,
            f"Pass@1 {bench.summary.pass_at_1:.1%} Pass@5 {bench.summary.pass_at_5:.1%}",
        )
    except Exception as exc:
        result.record(Phase2Step.BENCHMARK, False, str(exc))


def _resolve_paths(project_root: Path) -> dict[str, Path]:
    return {
        "published": project_root / "data" / "datasets",
        "held_out": project_root / "data" / "benchmarks" / "held-out-v1",
        "checkpoints": project_root / "data" / "checkpoints",
        "benchmark_output": project_root / "data" / "benchmarks",
        "smoke_output": project_root / ".local" / "training" / "smoke",
        "train_config": project_root / "config" / "train-v1.yaml",
        "benchmark_config": project_root / "config" / "benchmark-v1.yaml",
        "smoke_config": project_root / "config" / "smoke-train-v1.yaml",
        "events": project_root / "data" / "events" / "events.jsonl",
    }


def _finalize(result: Phase2PipelineResult, paths: dict[str, Path]) -> Phase2PipelineResult:
    report_path = project_root_review_path(paths)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "experimentId": result.experiment_id,
        "profile": result.profile,
        "datasetVersion": result.dataset_version,
        "trainRunId": result.train_run_id,
        "benchmarkRunId": result.benchmark_run_id,
        "failed": result.failed,
        "completedAt": datetime.now(UTC).isoformat(),
        "steps": [
            {"step": step.step.value, "success": step.success, "message": step.message}
            for step in result.steps
        ],
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return result


def project_root_review_path(paths: dict[str, Path]) -> Path:
    return paths["smoke_output"].parents[1] / "review" / "phase2-run-report.json"
