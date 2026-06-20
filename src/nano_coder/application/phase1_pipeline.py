"""Application service — Phase 1 per-language dataset pipeline (Stages 4–8)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from nano_coder.application.expand_dataset import load_expansion_config, run_expansion
from nano_coder.application.filter_synthetic import filter_synthetic_run
from nano_coder.application.manual_review_dataset import (
    build_auto_accept_decisions,
    prepare_manual_review,
    submit_manual_review,
)
from nano_coder.application.publish_dataset import publish_synthetic_dataset
from nano_coder.application.smoke_train import run_smoke_train
from nano_coder.domain.budget_guard import SeedCountInsufficient
from nano_coder.domain.dataset_publish_config import load_dataset_publish_config
from nano_coder.domain.manual_review_config import load_manual_review_config
from nano_coder.domain.phase1_config import (
    Phase1Config,
    format_dataset_version,
    format_run_id,
)
from nano_coder.domain.quality_gates_config import load_quality_gates_config
from nano_coder.domain.scope_boundary import load_scope_boundary
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy
from nano_coder.domain.smoke_train_config import load_smoke_train_config
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.teacher_client import build_teacher_client


class Phase1Step(StrEnum):
    GENERATE = "generate"
    FILTER = "filter"
    PREPARE_REVIEW = "prepareReview"
    SUBMIT_REVIEW = "submitReview"
    PUBLISH = "publish"
    SMOKE_TRAIN = "smokeTrain"


@dataclass(frozen=True)
class Phase1StepResult:
    step: Phase1Step
    success: bool
    message: str


@dataclass
class Phase1PipelineResult:
    language: TargetLanguage
    run_id: str
    dataset_version: str
    steps: list[Phase1StepResult] = field(default_factory=list)
    failed: bool = False

    def record(self, step: Phase1Step, success: bool, message: str) -> None:
        self.steps.append(Phase1StepResult(step=step, success=success, message=message))
        if not success:
            self.failed = True


def run_phase1_language_pipeline(
    *,
    language: TargetLanguage,
    config: Phase1Config,
    project_root: Path,
    run_id: str | None = None,
    dataset_version: str | None = None,
    target_count: int | None = None,
    max_batches: int | None = None,
    stop_after: Phase1Step | None = None,
) -> Phase1PipelineResult:
    run_id = run_id or format_run_id(config, language)
    dataset_version = dataset_version or format_dataset_version(config, language)
    goal = target_count or config.target_count

    result = Phase1PipelineResult(
        language=language,
        run_id=run_id,
        dataset_version=dataset_version,
    )

    paths = _resolve_paths(project_root)
    taxonomy = load_seed_taxonomy(paths["taxonomy"])
    scope = load_scope_boundary(paths["scope"])
    gates = load_quality_gates_config(paths["gates"])
    review_cfg = load_manual_review_config(paths["review_config"])
    publish_cfg = load_dataset_publish_config(paths["publish_config"])
    smoke_cfg = load_smoke_train_config(paths["smoke_config"])
    expansion_cfg = load_expansion_config(paths["generation"])

    try:
        _step_generate(
            result,
            language=language,
            run_id=run_id,
            goal=goal,
            max_batches=max_batches,
            config=config,
            expansion_cfg=expansion_cfg,
            paths=paths,
        )
        if result.failed or stop_after is Phase1Step.GENERATE:
            return _finalize(result, paths)

        _step_filter(
            result,
            run_id=run_id,
            config=config,
            paths=paths,
            taxonomy=taxonomy,
            scope=scope,
            gates=gates,
        )
        if result.failed or stop_after is Phase1Step.FILTER:
            return _finalize(result, paths)

        _step_prepare_review(result, run_id=run_id, review_cfg=review_cfg, paths=paths)
        if result.failed or stop_after is Phase1Step.PREPARE_REVIEW:
            return _finalize(result, paths)

        if config.auto_approve_review:
            _step_submit_review(
                result,
                run_id=run_id,
                config=config,
                review_cfg=review_cfg,
                paths=paths,
            )
            if result.failed or stop_after is Phase1Step.SUBMIT_REVIEW:
                return _finalize(result, paths)
        else:
            result.record(
                Phase1Step.SUBMIT_REVIEW,
                True,
                "skipped — operator must run submit_manual_review.py",
            )
            return _finalize(result, paths)

        _step_publish(
            result,
            run_id=run_id,
            dataset_version=dataset_version,
            config=config,
            publish_cfg=publish_cfg,
            paths=paths,
        )
        if result.failed or stop_after is Phase1Step.PUBLISH:
            return _finalize(result, paths)

        if config.run_smoke_train:
            _step_smoke_train(
                result,
                run_id=f"smoke-{run_id}",
                dataset_version=dataset_version,
                smoke_cfg=smoke_cfg,
                paths=paths,
            )
        else:
            result.record(Phase1Step.SMOKE_TRAIN, True, "skipped by config")

    except Exception as exc:  # noqa: BLE001
        result.record(Phase1Step.GENERATE, False, f"unexpected error: {exc}")
        result.failed = True

    return _finalize(result, paths)


def _finalize(result: Phase1PipelineResult, paths: dict[str, Path]) -> Phase1PipelineResult:
    _write_run_log(result, paths["phase1_log"] / f"{result.run_id}.json")
    return result


def _step_generate(
    result: Phase1PipelineResult,
    *,
    language: TargetLanguage,
    run_id: str,
    goal: int,
    max_batches: int | None,
    config: Phase1Config,
    expansion_cfg: Any,
    paths: dict[str, Path],
) -> None:
    teacher = build_teacher_client(
        language=language,
        dry_run=config.dry_run_generation,
        model=expansion_cfg.model,
        max_tokens=expansion_cfg.max_tokens,
    )
    try:
        expansion = run_expansion(
            run_id=run_id,
            language=language,
            seeds_root=paths["seeds"],
            reference_root=paths["reference"],
            prompt_dir=paths["prompts"],
            scope_path=paths["scope"],
            output_root=paths["raw"],
            config=expansion_cfg,
            teacher=teacher,
            target_count=goal,
            max_batches=max_batches,
        )
    except SeedCountInsufficient as exc:
        result.record(Phase1Step.GENERATE, False, str(exc))
        return

    if expansion.failed:
        result.record(Phase1Step.GENERATE, False, expansion.failure_reason or "generation failed")
        return

    result.record(
        Phase1Step.GENERATE,
        True,
        f"{expansion.candidate_count} candidates in {expansion.batch_count} batch(es)",
    )


def _step_filter(
    result: Phase1PipelineResult,
    *,
    run_id: str,
    config: Phase1Config,
    paths: dict[str, Path],
    taxonomy: Any,
    scope: Any,
    gates: Any,
) -> None:
    filter_result = filter_synthetic_run(
        raw_dir=paths["raw"] / run_id,
        output_root=paths["draft"],
        rejected_log=paths["rejected"],
        taxonomy=taxonomy,
        scope=scope,
        config=gates,
        seeds_root=paths["seeds"],
        eslint_config=paths["eslint"] if not config.skip_lint else None,
        skip_lint=config.skip_lint,
        language=result.language,
    )
    result.record(
        Phase1Step.FILTER,
        filter_result.accepted_count > 0,
        f"{filter_result.accepted_count}/{filter_result.candidate_count} accepted",
    )


def _step_prepare_review(
    result: Phase1PipelineResult,
    *,
    run_id: str,
    review_cfg: Any,
    paths: dict[str, Path],
) -> None:
    prepared = prepare_manual_review(
        run_id=run_id,
        draft_dir=paths["draft"] / run_id,
        review_root=paths["review_root"],
        config=review_cfg,
    )
    result.record(
        Phase1Step.PREPARE_REVIEW,
        True,
        f"sample {prepared.sample_size}/{prepared.accepted_count}",
    )


def _step_submit_review(
    result: Phase1PipelineResult,
    *,
    run_id: str,
    config: Phase1Config,
    review_cfg: Any,
    paths: dict[str, Path],
) -> None:
    queue_path = paths["review_root"] / run_id / "review-queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    decisions = build_auto_accept_decisions(queue["sampleExampleIds"])
    submitted = submit_manual_review(
        run_id=run_id,
        draft_dir=paths["draft"] / run_id,
        review_root=paths["review_root"],
        config=review_cfg,
        decisions=decisions,
        reviewed_by=config.operator_id,
    )
    result.record(
        Phase1Step.SUBMIT_REVIEW,
        submitted.final_state.value == "Completed",
        f"manual review {submitted.outcome.br005_manual_review_satisfied}",
    )


def _step_publish(
    result: Phase1PipelineResult,
    *,
    run_id: str,
    dataset_version: str,
    config: Phase1Config,
    publish_cfg: Any,
    paths: dict[str, Path],
) -> None:
    published = publish_synthetic_dataset(
        draft_id=run_id,
        dataset_version=dataset_version,
        draft_root=paths["draft"],
        published_root=paths["published"],
        config=publish_cfg,
        published_by=config.operator_id,
        events_log=paths["events"],
        skip_thresholds=config.skip_publish_thresholds,
    )
    result.record(
        Phase1Step.PUBLISH,
        True,
        f"published {published.example_count} examples as {dataset_version}",
    )


def _step_smoke_train(
    result: Phase1PipelineResult,
    *,
    run_id: str,
    dataset_version: str,
    smoke_cfg: Any,
    paths: dict[str, Path],
) -> None:
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
    result.record(
        Phase1Step.SMOKE_TRAIN,
        smoke.eval_summary.gate_satisfied,
        f"Pass@1 {smoke.eval_summary.pass_at_1:.1%} "
        f"gate={'pass' if smoke.eval_summary.gate_satisfied else 'fail'}",
    )


def _resolve_paths(project_root: Path) -> dict[str, Path]:
    return {
        "taxonomy": project_root / "config" / "seeds-v1" / "taxonomy.yaml",
        "scope": project_root / "config" / "scope-boundary.yaml",
        "gates": project_root / "config" / "quality-gates-v1.yaml",
        "review_config": project_root / "config" / "manual-review-v1.yaml",
        "publish_config": project_root / "config" / "dataset-publish-v1.yaml",
        "smoke_config": project_root / "config" / "smoke-train-v1.yaml",
        "generation": project_root / "config" / "generation-v1.yaml",
        "prompts": project_root / "config" / "prompts" / "v1",
        "seeds": project_root / "data" / "seeds",
        "reference": project_root / "data" / "seeds" / "reference",
        "raw": project_root / ".local" / "generation" / "raw",
        "draft": project_root / "data" / "datasets" / "draft",
        "rejected": project_root / ".local" / "generation" / "rejected.jsonl",
        "review_root": project_root / ".local" / "review",
        "published": project_root / "data" / "datasets",
        "events": project_root / "data" / "events" / "events.jsonl",
        "held_out": project_root / "data" / "benchmarks" / "held-out-v1",
        "checkpoints": project_root / "data" / "checkpoints",
        "smoke_output": project_root / ".local" / "training" / "smoke",
        "eslint": project_root / "config" / "eslint" / "eslint.config.js",
        "phase1_log": project_root / ".local" / "phase1" / "runs",
    }


def _write_run_log(result: Phase1PipelineResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "language": result.language.value,
        "runId": result.run_id,
        "datasetVersion": result.dataset_version,
        "failed": result.failed,
        "completedAt": datetime.now(UTC).isoformat(),
        "steps": [
            {"step": step.step.value, "success": step.success, "message": step.message}
            for step in result.steps
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
