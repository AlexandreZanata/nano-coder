"""Mock smoke trainer for dry-run pipeline validation (Stage 8)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.smoke_train_config import SmokeTrainConfig
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class MockTrainResult:
    checkpoint_dir: Path
    train_example_count: int
    steps: int
    final_loss: float
    duration_seconds: float
    backend: str


def run_mock_smoke_train(
    *,
    run_id: str,
    dataset_version: str,
    language: TargetLanguage,
    training_examples: list[dict[str, Any]],
    config: SmokeTrainConfig,
    checkpoint_root: Path,
) -> MockTrainResult:
    checkpoint_dir = checkpoint_root / run_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    steps = max(1, len(training_examples) // config.batch_size) * config.epochs
    manifest = {
        "runId": run_id,
        "datasetVersion": dataset_version,
        "targetLanguage": language.value,
        "studentModel": config.student_model,
        "compressionMethod": config.compression_method.value,
        "loraRank": config.lora_rank,
        "profile": config.profile,
        "trainExampleCount": len(training_examples),
        "epochs": config.epochs,
        "steps": steps,
        "finalLoss": 0.42,
        "backend": "mock-trainer",
        "completedAt": datetime.now(UTC).isoformat(),
    }
    (checkpoint_dir / "checkpoint-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (checkpoint_dir / "adapter-config.json").write_text(
        json.dumps(
            {
                "method": CompressionMethod.LORA.value,
                "rank": config.lora_rank,
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
        final_loss=0.42,
        duration_seconds=0.05,
        backend="mock-trainer",
    )


def mock_generate_response(
    task: dict[str, Any],
    *,
    language: TargetLanguage,
    task_index: int,
    pass_ratio: float = 0.70,
) -> str:
    """Generate deterministic mock student output for smoke evaluation."""
    criteria = task.get("acceptanceCriteria") or {}
    must_contain = [str(item) for item in criteria.get("mustContain", [])]
    should_pass = (task_index / max(1, task_index + 1)) < pass_ratio or task_index % 10 < 7

    if language is TargetLanguage.JAVASCRIPT:
        keywords = must_contain if should_pass else must_contain[:1]
        comment = "\n".join(f"  // covers {keyword}" for keyword in keywords)
        forbidden = '  // TODO placeholder\n' if not should_pass else ""
        return (
            f"/** Mock smoke response for {task.get('id', 'task')} */\n"
            f"export function smokeSolution() {{\n{comment}\n{forbidden}"
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
    return f"{forbidden}<#macro smokeSolution>\n{lines}\n</#macro>\n"
