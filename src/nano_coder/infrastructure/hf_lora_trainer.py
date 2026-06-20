"""Real LoRA / QLoRA / DoRA training via HuggingFace + PEFT."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.gpu_availability import peak_vram_gb, require_gpu_stack, reset_peak_vram_stats
from nano_coder.infrastructure.hf_model_registry import resolve_hf_model_id
from nano_coder.infrastructure.mock_trainer import MockTrainResult
from nano_coder.infrastructure.training_formatter import build_sft_records


def run_hf_lora_train(
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
    max_seq_length: int = 512,
    gradient_accumulation_steps: int = 4,
) -> MockTrainResult:
    require_gpu_stack()
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    from trl import SFTConfig, SFTTrainer

    if compression_method is CompressionMethod.FEW_SHOT:
        raise ValueError("FewShot baseline does not use GPU training")

    hf_model_id = resolve_hf_model_id(student_model)
    hf_token = os.environ.get("HF_TOKEN") or None
    checkpoint_dir = checkpoint_root / run_id
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    set_seed(seed)
    reset_peak_vram_stats()
    started = time.monotonic()

    use_qlora = compression_method is CompressionMethod.QLORA
    use_dora = compression_method is CompressionMethod.DORA
    effective_batch = max(1, batch_size)
    steps = min(
        max_steps,
        max(1, len(training_examples) // effective_batch) * max(1, epochs),
    )

    tokenizer = AutoTokenizer.from_pretrained(hf_model_id, token=hf_token, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model_kwargs: dict[str, Any] = {
        "token": hf_token,
        "trust_remote_code": True,
    }
    if use_qlora:
        from transformers import BitsAndBytesConfig

        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model_kwargs["device_map"] = "auto"
    else:
        model_kwargs["dtype"] = torch.float16

    model = AutoModelForCausalLM.from_pretrained(hf_model_id, **model_kwargs)
    if not use_qlora:
        model = model.to("cuda")

    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_rank * 2,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
        task_type="CAUSAL_LM",
        use_dora=use_dora,
    )
    model = get_peft_model(model, lora_config)
    trainable_param_count = sum(
        parameter.numel() for parameter in model.parameters() if parameter.requires_grad
    )

    dataset = Dataset.from_list(build_sft_records(training_examples))
    training_args = SFTConfig(
        output_dir=str(checkpoint_dir / "trainer-state"),
        max_steps=steps,
        per_device_train_batch_size=effective_batch,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=2e-4,
        logging_steps=max(1, steps // 10),
        save_strategy="no",
        report_to=[],
        seed=seed,
        fp16=True,
        max_length=max_seq_length,
        dataset_text_field="text",
        packing=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )
    train_output = trainer.train()
    final_loss = float(train_output.training_loss) if train_output.training_loss is not None else 0.0

    adapter_dir = checkpoint_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    duration_seconds = time.monotonic() - started
    peak_vram = peak_vram_gb()
    backend = _backend_name(compression_method)

    language = languages[0] if len(languages) == 1 else None
    manifest: dict[str, Any] = {
        "runId": run_id,
        "datasetVersion": dataset_version,
        "studentModel": student_model,
        "hfModelId": hf_model_id,
        "compressionMethod": compression_method.value,
        "loraRank": lora_rank,
        "profile": profile,
        "trainExampleCount": len(training_examples),
        "epochs": epochs,
        "steps": steps,
        "seed": seed,
        "finalLoss": round(final_loss, 6),
        "trainableParamCount": trainable_param_count,
        "peakVramGb": round(peak_vram, 3),
        "durationSeconds": round(duration_seconds, 3),
        "backend": backend,
        "adapterPath": "adapter",
        "completedAt": datetime.now(UTC).isoformat(),
    }
    if language is not None:
        manifest["targetLanguage"] = language.value
    manifest["dataSchedule"] = data_schedule.value

    (checkpoint_dir / "checkpoint-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    del trainer
    del model
    torch.cuda.empty_cache()

    return MockTrainResult(
        checkpoint_dir=checkpoint_dir,
        train_example_count=len(training_examples),
        steps=steps,
        final_loss=final_loss,
        duration_seconds=duration_seconds,
        peak_vram_gb=peak_vram,
        trainable_param_count=trainable_param_count,
        backend=backend,
    )


def _backend_name(compression_method: CompressionMethod) -> str:
    if compression_method is CompressionMethod.QLORA:
        return "hf-peft-qlora"
    if compression_method is CompressionMethod.DORA:
        return "hf-peft-dora"
    return "hf-peft-lora"
