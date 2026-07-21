"""QLoRA smoke trainer for specialized workers (HF PEFT — 8 GB safe)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_orchestrator.domain.train_example import TrainExample

# Map orchestrator worker ids → HuggingFace base ids.
HF_BASE_MODELS: dict[str, str] = {
    "qwen25-coder-0.5b": "Qwen/Qwen2.5-Coder-0.5B",
    "smollm2-360m": "HuggingFaceTB/SmolLM2-360M",
}


@dataclass(frozen=True, slots=True)
class TrainSmokeResult:
    run_id: str
    language: str
    base_model_id: str
    adapter_dir: Path
    steps: int
    example_count: int
    peak_vram_mb: float | None
    train_loss: float | None
    elapsed_s: float


def load_train_examples(jsonl_path: Path) -> list[TrainExample]:
    examples: list[TrainExample] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        examples.append(TrainExample.model_validate(json.loads(line)))
    return examples


def run_qlora_smoke(
    *,
    language: str,
    train_jsonl: Path,
    output_root: Path,
    base_worker_id: str = "qwen25-coder-0.5b",
    max_steps: int = 30,
    batch_size: int = 1,
    grad_accum: int = 4,
    max_seq_length: int = 512,
    lora_rank: int = 8,
    seed: int = 42,
) -> TrainSmokeResult:
    """Train a small QLoRA adapter; MUST fit RTX 4060 8 GB."""
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        set_seed,
    )
    from trl import SFTConfig, SFTTrainer

    if base_worker_id not in HF_BASE_MODELS:
        raise ValueError(f"unknown base worker: {base_worker_id}")
    hf_model_id = HF_BASE_MODELS[base_worker_id]
    examples = load_train_examples(train_jsonl)
    if not examples:
        raise ValueError(f"empty train set: {train_jsonl}")

    run_id = f"worker-{language}-qlora-smoke"
    run_dir = output_root / run_id
    adapter_dir = run_dir / "adapter"
    run_dir.mkdir(parents=True, exist_ok=True)

    set_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()

    started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(hf_model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        hf_model_id,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        ),
        device_map="auto",
        trust_remote_code=True,
        token=os.environ.get("HF_TOKEN") or None,
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(
        model,
        LoraConfig(
            r=lora_rank,
            lora_alpha=lora_rank * 2,
            lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )

    records = [{"text": ex.to_sft_text()} for ex in examples]
    steps = min(max_steps, max(1, len(records)))
    trainer = SFTTrainer(
        model=model,
        args=SFTConfig(
            output_dir=str(run_dir / "trainer-state"),
            max_steps=steps,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=grad_accum,
            learning_rate=2e-4,
            logging_steps=max(1, steps // 5),
            save_strategy="no",
            report_to=[],
            seed=seed,
            fp16=False,
            bf16=False,
            max_length=max_seq_length,
            dataset_text_field="text",
            packing=False,
        ),
        train_dataset=Dataset.from_list(records),
        processing_class=tokenizer,
    )
    train_output = trainer.train()
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    peak_vram_mb = None
    if torch.cuda.is_available():
        peak_vram_mb = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 1)

    result = TrainSmokeResult(
        run_id=run_id,
        language=language,
        base_model_id=hf_model_id,
        adapter_dir=adapter_dir,
        steps=steps,
        example_count=len(examples),
        peak_vram_mb=peak_vram_mb,
        train_loss=(
            float(train_output.training_loss)
            if train_output.training_loss is not None
            else None
        ),
        elapsed_s=round(time.perf_counter() - started, 2),
    )
    _write_manifest(run_dir, result)
    return result


def _write_manifest(run_dir: Path, result: TrainSmokeResult) -> None:
    payload: dict[str, Any] = {
        "run_id": result.run_id,
        "language": result.language,
        "base_model_id": result.base_model_id,
        "adapter_dir": str(result.adapter_dir),
        "steps": result.steps,
        "example_count": result.example_count,
        "peak_vram_mb": result.peak_vram_mb,
        "train_loss": result.train_loss,
        "elapsed_s": result.elapsed_s,
        "method": "hf-peft-qlora",
        "notes": "Unsloth optional; HF PEFT QLoRA is the validated 8GB path in this repo",
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
