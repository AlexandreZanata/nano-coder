"""Mock trainer for dry-run pipeline validation (Stage 8, Phase 2 UC-003)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.smoke_train_config import SmokeTrainConfig
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class MockTrainResult:
    checkpoint_dir: Path
    train_example_count: int
    steps: int
    final_loss: float
    duration_seconds: float
    peak_vram_gb: float
    trainable_param_count: int
    backend: str


class CheckpointNotFoundError(Exception):
    """Benchmark cannot start — checkpoint manifest missing."""


def run_mock_smoke_train(
    *,
    run_id: str,
    dataset_version: str,
    language: TargetLanguage,
    training_examples: list[dict[str, Any]],
    config: SmokeTrainConfig,
    checkpoint_root: Path,
) -> MockTrainResult:
    steps = max(1, len(training_examples) // config.batch_size) * config.epochs
    return _write_mock_checkpoint(
        run_id=run_id,
        dataset_version=dataset_version,
        language=language,
        training_examples=training_examples,
        compression_method=config.compression_method,
        lora_rank=config.lora_rank,
        profile=config.profile,
        student_model=config.student_model,
        steps=steps,
        epochs=config.epochs,
        checkpoint_root=checkpoint_root,
        data_schedule=None,
        seed=config.random_seed,
    )


def run_mock_train(
    *,
    run_id: str,
    dataset_version: str,
    languages: tuple[TargetLanguage, ...],
    training_examples: list[dict[str, Any]],
    compression_method: CompressionMethod,
    lora_rank: int,
    profile: str,
    student_model: str,
    data_schedule: DataSchedule,
    max_steps: int,
    batch_size: int,
    epochs: int,
    seed: int,
    checkpoint_root: Path,
) -> MockTrainResult:
    steps = min(max_steps, max(1, len(training_examples) // batch_size) * epochs)
    language = languages[0] if len(languages) == 1 else None
    return _write_mock_checkpoint(
        run_id=run_id,
        dataset_version=dataset_version,
        language=language,
        training_examples=training_examples,
        compression_method=compression_method,
        lora_rank=lora_rank,
        profile=profile,
        student_model=student_model,
        steps=steps,
        epochs=epochs,
        checkpoint_root=checkpoint_root,
        data_schedule=data_schedule,
        seed=seed,
    )


def load_checkpoint_manifest(checkpoint_dir: Path) -> dict[str, Any]:
    path = checkpoint_dir / "checkpoint-manifest.json"
    if not path.is_file():
        raise CheckpointNotFoundError(f"checkpoint manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_mock_checkpoint(
    *,
    run_id: str,
    dataset_version: str,
    language: TargetLanguage | None,
    training_examples: list[dict[str, Any]],
    compression_method: CompressionMethod,
    lora_rank: int,
    profile: str,
    student_model: str,
    steps: int,
    epochs: int,
    checkpoint_root: Path,
    data_schedule: DataSchedule | None,
    seed: int,
) -> MockTrainResult:
    checkpoint_dir = checkpoint_root / run_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    trainable_param_count = _trainable_param_count(compression_method, lora_rank)
    peak_vram_gb = _peak_vram_gb(compression_method, profile)
    duration_seconds = _duration_seconds(compression_method, steps)

    manifest: dict[str, Any] = {
        "runId": run_id,
        "datasetVersion": dataset_version,
        "studentModel": student_model,
        "compressionMethod": compression_method.value,
        "loraRank": lora_rank,
        "profile": profile,
        "trainExampleCount": len(training_examples),
        "epochs": epochs,
        "steps": steps,
        "seed": seed,
        "finalLoss": 0.38,
        "trainableParamCount": trainable_param_count,
        "peakVramGb": peak_vram_gb,
        "durationSeconds": round(duration_seconds, 3),
        "backend": "mock-trainer",
        "completedAt": datetime.now(UTC).isoformat(),
    }
    if language is not None:
        manifest["targetLanguage"] = language.value
    if data_schedule is not None:
        manifest["dataSchedule"] = data_schedule.value

    (checkpoint_dir / "checkpoint-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (checkpoint_dir / "adapter-config.json").write_text(
        json.dumps(
            {
                "method": compression_method.value,
                "rank": lora_rank,
                "targetModules": ["q_proj", "v_proj"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return MockTrainResult(
        checkpoint_dir=checkpoint_dir,
        train_example_count=len(training_examples),
        steps=steps,
        final_loss=0.38,
        duration_seconds=duration_seconds,
        peak_vram_gb=peak_vram_gb,
        trainable_param_count=trainable_param_count,
        backend="mock-trainer",
    )


def mock_generate_response(
    task: dict[str, Any],
    *,
    language: TargetLanguage,
    task_index: int,
    pass_ratio: float = 0.70,
    sample_index: int = 0,
) -> str:
    """Generate deterministic mock student output for smoke/benchmark evaluation."""
    criteria = task.get("acceptanceCriteria") or {}
    must_contain = [str(item) for item in criteria.get("mustContain", [])]
    score = (task_index + sample_index) % 10
    should_pass = score / 10.0 < pass_ratio

    if language is TargetLanguage.JAVASCRIPT:
        keywords = must_contain if should_pass else must_contain[:1]
        comment = "\n".join(f"  // covers {keyword}" for keyword in keywords)
        forbidden = '  // TODO placeholder\n' if not should_pass else ""
        return (
            f"/** Mock response for {task.get('id', 'task')} sample {sample_index} */\n"
            f"export function solution() {{\n{comment}\n{forbidden}"
            f"  return true;\n}}\n"
        )
    if language is TargetLanguage.HTML:
        keywords = must_contain if should_pass else must_contain[:1]
        body = "\n".join(f"    <p>{keyword}</p>" for keyword in keywords)
        forbidden = "    <!-- TODO -->\n" if not should_pass else ""
        return (
            f"<!DOCTYPE html>\n<html lang=\"en\">\n<head><meta charset=\"utf-8\" /></head>\n"
            f"<body>\n{forbidden}{body}\n</body>\n</html>\n"
        )

    keywords = must_contain if should_pass else must_contain[:1]
    lines = "\n".join(f"  <#-- {keyword} -->" for keyword in keywords)
    forbidden = "<#-- TODO -->\n" if not should_pass else ""
    return f"{forbidden}<#macro solution>\n{lines}\n</#macro>\n"


def mock_pass_ratio(compression_method: CompressionMethod) -> float:
    ratios = {
        CompressionMethod.FEW_SHOT: 0.42,
        CompressionMethod.LORA: 0.72,
        CompressionMethod.QLORA: 0.68,
        CompressionMethod.DORA: 0.74,
    }
    return ratios.get(compression_method, 0.70)


def _trainable_param_count(compression_method: CompressionMethod, lora_rank: int) -> int:
    base = lora_rank * lora_rank * 4096
    if compression_method is CompressionMethod.DORA:
        return int(base * 1.05)
    if compression_method is CompressionMethod.QLORA:
        return base
    return base


def _peak_vram_gb(compression_method: CompressionMethod, profile: str) -> float:
    if compression_method is CompressionMethod.FEW_SHOT:
        return 0.0
    if compression_method is CompressionMethod.QLORA:
        return 2.4 if profile == "smoke" else 3.1
    if compression_method is CompressionMethod.DORA:
        return 3.4 if profile == "smoke" else 5.0
    return 3.2 if profile == "smoke" else 4.8


def _duration_seconds(compression_method: CompressionMethod, steps: int) -> float:
    base = 0.05 + steps * 0.001
    if compression_method is CompressionMethod.QLORA:
        return base * 1.15
    if compression_method is CompressionMethod.DORA:
        return base * 1.08
    return base

