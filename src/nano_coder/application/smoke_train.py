"""Application service — smoke LoRA train and held-out evaluation (Stage 8)."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.published_dataset import PublishedDataset, load_published_dataset
from nano_coder.domain.smoke_eval import (
    SmokeEvalSummary,
    evaluate_smoke_task,
    load_held_out_tasks,
    summarize_smoke_eval,
)
from nano_coder.domain.smoke_train_config import SmokeTrainConfig
from nano_coder.domain.training_run import TrainingRun, TrainingRunState
from nano_coder.infrastructure.mock_trainer import mock_generate_response, run_mock_smoke_train


@dataclass(frozen=True)
class SmokeTrainResult:
    run_id: str
    dataset_version: str
    training_state: TrainingRunState
    train_example_count: int
    checkpoint_dir: Path
    eval_summary: SmokeEvalSummary
    manifest_path: Path
    iteration_required: bool


def run_smoke_train(
    *,
    run_id: str,
    dataset_version: str,
    published_root: Path,
    held_out_root: Path,
    checkpoint_root: Path,
    output_root: Path,
    config: SmokeTrainConfig,
    dry_run: bool = True,
) -> SmokeTrainResult:
    if not dry_run:
        raise NotImplementedError(
            "GPU smoke training requires torch/transformers — use --dry-run for pipeline validation"
        )

    dataset = load_published_dataset(published_root, dataset_version)
    training_examples = _sample_training_examples(dataset, config)
    tasks = load_held_out_tasks(
        held_out_root,
        dataset.target_language,
        limit=config.smoke_eval_tasks,
    )

    run = TrainingRun(run_id, dataset_version)
    run.transition(TrainingRunState.RUNNING)

    train_result = run_mock_smoke_train(
        run_id=run_id,
        dataset_version=dataset_version,
        language=dataset.target_language,
        training_examples=training_examples,
        config=config,
        checkpoint_root=checkpoint_root,
    )

    eval_results = []
    for index, task in enumerate(tasks):
        generated = mock_generate_response(
            task,
            language=dataset.target_language,
            task_index=index,
        )
        eval_results.append(
            evaluate_smoke_task(task, generated, language=dataset.target_language)
        )

    eval_summary = summarize_smoke_eval(
        eval_results,
        min_pass_at_1=config.min_pass_at_1,
    )
    final_state = (
        TrainingRunState.COMPLETED if eval_summary.gate_satisfied else TrainingRunState.FAILED
    )
    run.transition(final_state)

    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "smoke-train-manifest.json"
    manifest = _build_manifest(
        run_id=run_id,
        dataset=dataset,
        config=config,
        train_result=train_result,
        eval_summary=eval_summary,
        final_state=final_state,
        dry_run=dry_run,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    eval_path = output_dir / "smoke-eval.jsonl"
    _write_eval_jsonl(eval_path, tasks, eval_results)

    checkpoint_manifest = train_result.checkpoint_dir / "smoke-train-manifest.json"
    checkpoint_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return SmokeTrainResult(
        run_id=run_id,
        dataset_version=dataset_version,
        training_state=final_state,
        train_example_count=train_result.train_example_count,
        checkpoint_dir=train_result.checkpoint_dir,
        eval_summary=eval_summary,
        manifest_path=manifest_path,
        iteration_required=not eval_summary.gate_satisfied,
    )


def _sample_training_examples(
    dataset: PublishedDataset,
    config: SmokeTrainConfig,
) -> list[dict[str, Any]]:
    examples = list(dataset.examples)
    rng = random.Random(config.random_seed)
    rng.shuffle(examples)
    limit = min(len(examples), config.max_train_examples)
    return examples[:limit]


def _build_manifest(
    *,
    run_id: str,
    dataset: PublishedDataset,
    config: SmokeTrainConfig,
    train_result: Any,
    eval_summary: SmokeEvalSummary,
    final_state: TrainingRunState,
    dry_run: bool,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "runId": run_id,
        "datasetVersion": dataset.dataset_version,
        "targetLanguage": dataset.target_language.value,
        "profile": config.profile,
        "studentModel": config.student_model,
        "compressionMethod": config.compression_method.value,
        "trainExampleCount": train_result.train_example_count,
        "smokeEvalTasks": eval_summary.task_count,
        "passAt1": round(eval_summary.pass_at_1, 4),
        "minPassAt1": config.min_pass_at_1,
        "gateSatisfied": eval_summary.gate_satisfied,
        "trainingState": final_state.value,
        "backend": train_result.backend,
        "dryRun": dry_run,
        "completedAt": datetime.now(UTC).isoformat(),
        "checkpointDir": str(train_result.checkpoint_dir),
    }
    if not eval_summary.gate_satisfied:
        manifest["iterationHints"] = list(config.iteration_hints)
    return manifest


def _write_eval_jsonl(
    path: Path,
    tasks: list[dict[str, Any]],
    results: list[Any],
) -> None:
    lines = []
    for task, result in zip(tasks, results, strict=True):
        lines.append(
            json.dumps(
                {
                    "taskId": result.task_id,
                    "instruction": task.get("instruction"),
                    "passed": result.passed,
                    "reason": result.reason,
                },
                ensure_ascii=False,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
