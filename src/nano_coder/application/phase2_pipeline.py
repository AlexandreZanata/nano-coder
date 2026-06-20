"""Phase 2 pipeline — delegates to generalized method experiment runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from nano_coder.application.method_experiment_pipeline import (
    MethodExperimentResult,
    MethodExperimentStep,
    run_method_experiment,
)
from nano_coder.domain.experiment_config import ExperimentSpec
from nano_coder.domain.phase2_config import Phase2Config


class Phase2Step(StrEnum):
    SMOKE_TRAIN = MethodExperimentStep.SMOKE_TRAIN.value
    TRAIN = MethodExperimentStep.TRAIN.value
    BENCHMARK = MethodExperimentStep.BENCHMARK.value


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
    dry_run: bool = True,
) -> Phase2PipelineResult:
    method_result = run_method_experiment(
        spec=_to_experiment_spec(config),
        project_root=project_root,
        profile=profile,
        dataset_version=dataset_version,
        train_run_id=train_run_id,
        benchmark_run_id=benchmark_run_id,
        run_smoke=run_smoke,
        stop_after=MethodExperimentStep(stop_after.value) if stop_after else None,
        dry_run=dry_run,
    )
    return _from_method_result(method_result)


def _to_experiment_spec(config: Phase2Config) -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id=config.experiment_id,
        compression_method=config.compression_method,
        evidence_level=config.evidence_level,
        method_slug="lora",
        dataset_version=config.dataset_version,
        smoke_dataset_version=config.smoke_dataset_version,
        student_model=config.student_model,
        data_schedule=config.data_schedule,
        lora_rank=config.lora_rank,
        held_out_test_set_version=config.held_out_test_set_version,
        run_id_templates=config.run_id_templates,
        skip_train=False,
    )


def _from_method_result(result: MethodExperimentResult) -> Phase2PipelineResult:
    pipeline = Phase2PipelineResult(
        experiment_id=result.experiment_id,
        profile=result.profile,
        dataset_version=result.dataset_version,
        train_run_id=result.train_run_id,
        benchmark_run_id=result.benchmark_run_id,
        failed=result.failed,
    )
    pipeline.steps = [
        Phase2StepResult(
            step=Phase2Step(step.step.value),
            success=step.success,
            message=step.message,
        )
        for step in result.steps
    ]
    return pipeline
