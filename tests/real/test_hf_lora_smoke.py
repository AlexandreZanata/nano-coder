"""Real GPU smoke — LoRA train + inference (skipped without GPU stack)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.gpu_availability import is_gpu_stack_available
from nano_coder.infrastructure.hf_lora_trainer import run_hf_lora_train
from nano_coder.infrastructure.hf_student_inference import generate_student_samples
from nano_coder.infrastructure.mock_trainer import load_checkpoint_manifest

pytestmark = pytest.mark.real


@pytest.mark.skipif(not is_gpu_stack_available(), reason="GPU stack unavailable")
def test_real_lora_smoke_train_and_generate(tmp_path: Path) -> None:
    examples = [
        {
            "instruction": "Write a JavaScript function that returns 42.",
            "code": "export function answer() {\n  return 42;\n}\n",
        },
        {
            "instruction": "Write a JavaScript function that adds two numbers.",
            "code": "export function add(a, b) {\n  return a + b;\n}\n",
        },
    ]
    result = run_hf_lora_train(
        run_id="real-smoke-test",
        dataset_version="ds-real-smoke",
        languages=(TargetLanguage.JAVASCRIPT,),
        training_examples=examples,
        compression_method=CompressionMethod.LORA,
        lora_rank=8,
        profile="ci",
        student_model="Qwen2.5-Coder-0.5B",
        data_schedule=DataSchedule.MIXED_LANGUAGES,
        max_steps=2,
        batch_size=1,
        epochs=1,
        seed=42,
        checkpoint_root=tmp_path,
        max_seq_length=256,
        gradient_accumulation_steps=1,
    )
    assert result.steps == 2
    assert result.checkpoint_dir.is_dir()
    manifest = load_checkpoint_manifest(result.checkpoint_dir)
    assert manifest["backend"] == "hf-peft-lora"
    assert (result.checkpoint_dir / "adapter").is_dir()

    samples = generate_student_samples(
        result.checkpoint_dir,
        instruction="Write a JavaScript function that returns 42.",
        num_samples=1,
        max_new_tokens=64,
    )
    assert samples
    assert isinstance(samples[0], str)
    if os.environ.get("HF_TOKEN"):
        assert len(samples[0]) > 0
