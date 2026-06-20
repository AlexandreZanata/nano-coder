"""Application service — fine-tune student model (UC-003, Phase 2)."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.train_config import (
    TrainConfig,
    resolve_train_profile,
    validate_train_hyperparams,
)
from nano_coder.domain.training_dataset import load_training_dataset
from nano_coder.domain.training_run import TrainingRun, TrainingRunState
from nano_coder.infrastructure.mock_trainer import run_mock_train


@dataclass(frozen=True)
class TrainResult:
    run_id: str
    dataset_version: str
    training_state: TrainingRunState
    train_example_count: int
    checkpoint_dir: Path
    manifest_path: Path
    peak_vram_gb: float
    duration_seconds: float
    trainable_param_count: int


def run_train(
    *,
    run_id: str,
    dataset_version: str,
    compression_method: CompressionMethod,
    student_model: str,
    data_schedule: DataSchedule,
    published_root: Path,
    checkpoint_root: Path,
    config: TrainConfig,
    profile: str,
    lora_rank: int | None = None,
    seed: int | None = None,
    events_log: Path | None = None,
    dry_run: bool = True,
    evidence_level: str = "Established",
) -> TrainResult:
    if not dry_run:
        raise NotImplementedError(
            "GPU training requires torch/transformers/peft — use dry-run for pipeline validation"
        )

    rank = lora_rank if lora_rank is not None else config.lora_rank
    validate_train_hyperparams(compression_method=compression_method, lora_rank=rank)
    train_profile = resolve_train_profile(config, profile)
    chosen_seed = seed if seed is not None else train_profile.seeds[0]

    dataset = load_training_dataset(published_root, dataset_version)
    training_examples = _sample_training_examples(
        dataset.examples,
        limit=train_profile.max_train_examples,
        seed=chosen_seed,
    )

    run = TrainingRun(run_id, dataset_version)
    run.transition(TrainingRunState.RUNNING)
    _append_event(
        events_log,
        {
            "event": "TrainingRunStarted",
            "runId": run_id,
            "datasetVersion": dataset_version,
            "compressionMethod": compression_method.value,
            "profile": profile,
            "seed": chosen_seed,
        },
    )

    train_result = run_mock_train(
        run_id=run_id,
        dataset_version=dataset_version,
        languages=dataset.target_languages,
        training_examples=training_examples,
        compression_method=compression_method,
        lora_rank=rank,
        profile=profile,
        student_model=student_model,
        data_schedule=data_schedule,
        max_steps=train_profile.max_steps,
        batch_size=config.batch_size,
        epochs=config.epochs,
        seed=chosen_seed,
        checkpoint_root=checkpoint_root,
    )

    run.transition(TrainingRunState.COMPLETED)
    manifest_path = train_result.checkpoint_dir / "checkpoint-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["trainingState"] = run.state.value
    manifest["dryRun"] = dry_run
    manifest["evidenceLevel"] = evidence_level
    manifest["heldOutTestSetVersion"] = "held-out-v1"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    _append_event(
        events_log,
        {
            "event": "TrainingRunCompleted",
            "runId": run_id,
            "datasetVersion": dataset_version,
            "durationSeconds": train_result.duration_seconds,
            "peakVramGb": train_result.peak_vram_gb,
            "trainableParamCount": train_result.trainable_param_count,
        },
    )

    return TrainResult(
        run_id=run_id,
        dataset_version=dataset_version,
        training_state=run.state,
        train_example_count=train_result.train_example_count,
        checkpoint_dir=train_result.checkpoint_dir,
        manifest_path=manifest_path,
        peak_vram_gb=train_result.peak_vram_gb,
        duration_seconds=train_result.duration_seconds,
        trainable_param_count=train_result.trainable_param_count,
    )


def _sample_training_examples(
    examples: tuple[dict[str, Any], ...],
    *,
    limit: int,
    seed: int,
) -> list[dict[str, Any]]:
    items = list(examples)
    rng = random.Random(seed)
    rng.shuffle(items)
    return items[: min(len(items), limit)]


def _append_event(path: Path | None, event: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    event.setdefault("timestamp", datetime.now(UTC).isoformat())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
