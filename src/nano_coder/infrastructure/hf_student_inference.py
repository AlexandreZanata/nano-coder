"""Real student inference from HF base model + PEFT adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_coder.infrastructure.gpu_availability import require_gpu_stack
from nano_coder.infrastructure.hf_model_registry import resolve_hf_model_id
from nano_coder.infrastructure.mock_trainer import load_checkpoint_manifest
from nano_coder.infrastructure.training_formatter import format_sft_text


@dataclass
class _LoadedStudent:
    model: Any
    tokenizer: Any
    manifest: dict[str, Any]


_CACHE: dict[str, _LoadedStudent] = {}


def clear_inference_cache() -> None:
    _CACHE.clear()


def generate_student_samples(
    checkpoint_dir: Path,
    *,
    instruction: str,
    num_samples: int,
    max_new_tokens: int = 256,
    temperature: float = 0.7,
    top_p: float = 0.95,
) -> list[str]:
    loaded = _load_student(checkpoint_dir)
    prompt = format_sft_text({"instruction": instruction, "code": ""}).rstrip() + "\n"
    inputs = loaded.tokenizer(prompt, return_tensors="pt").to(loaded.model.device)

    import torch

    samples: list[str] = []
    for sample_index in range(num_samples):
        do_sample = num_samples > 1 or sample_index > 0
        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "pad_token_id": loaded.tokenizer.pad_token_id,
            "eos_token_id": loaded.tokenizer.eos_token_id,
        }
        if do_sample:
            gen_kwargs.update(
                {
                    "do_sample": True,
                    "temperature": temperature,
                    "top_p": top_p,
                }
            )
        else:
            gen_kwargs["do_sample"] = False

        with torch.no_grad():
            output = loaded.model.generate(**inputs, **gen_kwargs)

        decoded = loaded.tokenizer.decode(output[0], skip_special_tokens=True)
        samples.append(_extract_response(decoded, prompt))

    return samples


def _load_student(checkpoint_dir: Path) -> _LoadedStudent:
    key = str(checkpoint_dir.resolve())
    if key in _CACHE:
        return _CACHE[key]

    require_gpu_stack()
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    manifest = load_checkpoint_manifest(checkpoint_dir)
    hf_model_id = manifest.get("hfModelId") or resolve_hf_model_id(str(manifest["studentModel"]))
    adapter_rel = manifest.get("adapterPath", "adapter")
    adapter_dir = checkpoint_dir / adapter_rel
    if not adapter_dir.is_dir():
        raise FileNotFoundError(f"adapter not found: {adapter_dir}")

    hf_token = os.environ.get("HF_TOKEN") or None
    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, token=hf_token, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        hf_model_id,
        token=hf_token,
        dtype=torch.float16,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, adapter_dir)
    model = model.to("cuda")
    model.eval()

    loaded = _LoadedStudent(model=model, tokenizer=tokenizer, manifest=manifest)
    _CACHE[key] = loaded
    return loaded


def _extract_response(decoded: str, prompt: str) -> str:
    marker = "### Response:"
    if marker in decoded:
        return decoded.split(marker, maxsplit=1)[1].strip()
    if decoded.startswith(prompt):
        return decoded[len(prompt) :].strip()
    return decoded.strip()
