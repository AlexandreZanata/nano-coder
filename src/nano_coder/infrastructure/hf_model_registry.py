"""Resolve short student model ids to HuggingFace hub ids."""

from __future__ import annotations

STUDENT_MODEL_IDS: dict[str, str] = {
    "Qwen2.5-Coder-0.5B": "Qwen/Qwen2.5-Coder-0.5B",
    "Qwen2.5-Coder-1.5B": "Qwen/Qwen2.5-Coder-1.5B",
}


def resolve_hf_model_id(student_model: str) -> str:
    if "/" in student_model:
        return student_model
    try:
        return STUDENT_MODEL_IDS[student_model]
    except KeyError as exc:
        raise ValueError(f"Unknown student model: {student_model}") from exc
