"""Application service — method experiment pipeline (Phase 2/3, UC-003/UC-004)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from nano_coder.application.benchmark import run_benchmark
from nano_coder.application.fewshot_baseline import run_fewshot_baseline
from nano_coder.application.smoke_train import run_smoke_train
from nano_coder.application.train import run_train
from nano_coder.domain.benchmark_config import BenchmarkConfig, load_benchmark_config
from nano_coder.domain.experiment_config import ExperimentSpec, format_run_id
from nano_coder.domain.smoke_train_config import SmokeTrainConfig, load_smoke_train_config
from nano_coder.domain.train_config import TrainConfig, load_train_config
from nano_coder.domain.training_run import TrainingRunState


class MethodExperimentStep(StrEnum):
    SMOKE_TRAIN = "smokeTrain"
    TRAIN = "train"
    BENCHMARK = "benchmark"


@dataclass(frozen=True)
class MethodExperimentStepResult:
    step: MethodExperimentStep
    success: bool
    message: str


@dataclass
class MethodExperimentResult:
    experiment_id: str
    compression_method: str
    profile: str
    dataset_version: str
    train_run_id: str
    benchmark_run_id: str
    failed: bool = False
    steps: list[MethodExperimentStepResult] = field(default_factory=list)

    def record(self, step: MethodExperimentStep, success: bool, message: str) -> None:
        self.steps.append(MethodExperimentStepResult(step=step, success=success, message=message))
        if not success:
            self.failed = True


def run_method_experiment(
    *,
    spec: ExperimentSpec,
    project_root: Path,
    profile: str = "smoke",
    dataset_version: str | None = None,
    train_run_id: str | None = None,
    benchmark_run_id: str | None = None,
    run_smoke: bool = False,
    stop_after: MethodExperimentStep | None = None,
    dry_run: bool = True,
) -> MethodExperimentResult:
    paths = resolve_experiment_paths(project_root)
    version = dataset_version or spec.dataset_version
    resolved_train_id = train_run_id or format_run_id(
        spec.run_id_templates["train"],
        profile=profile,
    )
    resolved_bench_id = benchmark_run_id or format_run_id(
        spec.run_id_templates["benchmark"],
        profile=profile,
    )

    result = MethodExperimentResult(
        experiment_id=spec.experiment_id,
        compression_method=spec.compression_method.value,
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
            run_id=format_run_id("smoke-{method}-{profile}-001", profile=profile).replace(
                "{method}", spec.method_slug
            ),
            dataset_version=spec.smoke_dataset_version,
            smoke_cfg=smoke_cfg,
            paths=paths,
        )
        if result.failed or stop_after is MethodExperimentStep.SMOKE_TRAIN:
            return _finalize(result, paths)

    if spec.skip_train:
        _step_fewshot_baseline(
            result,
            run_id=resolved_train_id,
            spec=spec,
            profile=profile,
            paths=paths,
        )
    else:
        _step_train(
            result,
            run_id=resolved_train_id,
            dataset_version=version,
            spec=spec,
            train_cfg=train_cfg,
            profile=profile,
            paths=paths,
            dry_run=dry_run,
        )
    if result.failed or stop_after is MethodExperimentStep.TRAIN:
        return _finalize(result, paths)

    _step_benchmark(
        result,
        run_id=resolved_bench_id,
        train_run_id=resolved_train_id,
        spec=spec,
        bench_cfg=bench_cfg,
        paths=paths,
        dry_run=dry_run,
    )
    return _finalize(result, paths)


def resolve_experiment_paths(project_root: Path) -> dict[str, Path]:
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
        "review": project_root / ".local" / "review",
    }


def _step_smoke_train(
    result: MethodExperimentResult,
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
            MethodExperimentStep.SMOKE_TRAIN,
            smoke.training_state is TrainingRunState.COMPLETED,
            f"Pass@1 {smoke.eval_summary.pass_at_1:.1%} gate={gate}",
        )
    except Exception as exc:
        result.record(MethodExperimentStep.SMOKE_TRAIN, False, str(exc))


def _step_train(
    result: MethodExperimentResult,
    *,
    run_id: str,
    dataset_version: str,
    spec: ExperimentSpec,
    train_cfg: TrainConfig,
    profile: str,
    paths: dict[str, Path],
    dry_run: bool,
) -> None:
    try:
        train = run_train(
            run_id=run_id,
            dataset_version=dataset_version,
            compression_method=spec.compression_method,
            student_model=spec.student_model,
            data_schedule=spec.data_schedule,
            published_root=paths["published"],
            checkpoint_root=paths["checkpoints"],
            config=train_cfg,
            profile=profile,
            lora_rank=spec.lora_rank,
            events_log=paths["events"],
            dry_run=dry_run,
            evidence_level=spec.evidence_level,
        )
        result.record(
            MethodExperimentStep.TRAIN,
            train.training_state is TrainingRunState.COMPLETED,
            f"trained {train.train_example_count} examples → {train.checkpoint_dir.name}",
        )
    except Exception as exc:
        result.record(MethodExperimentStep.TRAIN, False, str(exc))


def _step_fewshot_baseline(
    result: MethodExperimentResult,
    *,
    run_id: str,
    spec: ExperimentSpec,
    profile: str,
    paths: dict[str, Path],
) -> None:
    try:
        baseline = run_fewshot_baseline(
            run_id=run_id,
            dataset_version=spec.dataset_version,
            student_model=spec.student_model,
            data_schedule=spec.data_schedule,
            checkpoint_root=paths["checkpoints"],
            profile=profile,
            evidence_level=spec.evidence_level,
            events_log=paths["events"],
        )
        result.record(
            MethodExperimentStep.TRAIN,
            True,
            f"fewshot baseline → {baseline.checkpoint_dir.name}",
        )
    except Exception as exc:
        result.record(MethodExperimentStep.TRAIN, False, str(exc))


def _step_benchmark(
    result: MethodExperimentResult,
    *,
    run_id: str,
    train_run_id: str,
    spec: ExperimentSpec,
    bench_cfg: BenchmarkConfig,
    paths: dict[str, Path],
    dry_run: bool,
) -> None:
    try:
        bench = run_benchmark(
            run_id=run_id,
            checkpoint_dir=paths["checkpoints"] / train_run_id,
            held_out_root=paths["held_out"],
            output_root=paths["benchmark_output"],
            config=bench_cfg,
            test_set_version=spec.held_out_test_set_version,
            events_log=paths["events"],
            dry_run=dry_run,
        )
        _enrich_benchmark_results(bench.results_path, spec=spec)
        result.record(
            MethodExperimentStep.BENCHMARK,
            True,
            f"Pass@1 {bench.summary.pass_at_1:.1%} Pass@5 {bench.summary.pass_at_5:.1%}",
        )
    except Exception as exc:
        result.record(MethodExperimentStep.BENCHMARK, False, str(exc))


def _enrich_benchmark_results(path: Path, *, spec: ExperimentSpec) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["experimentId"] = spec.experiment_id
    payload["evidenceLevel"] = spec.evidence_level
    payload["loraRank"] = spec.lora_rank if not spec.skip_train else None
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _finalize(result: MethodExperimentResult, paths: dict[str, Path]) -> MethodExperimentResult:
    report_path = paths["review"] / f"{result.experiment_id}-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "experimentId": result.experiment_id,
        "compressionMethod": result.compression_method,
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
