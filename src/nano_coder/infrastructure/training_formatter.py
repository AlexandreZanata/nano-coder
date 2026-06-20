"""Format published examples for SFT (instruction → code)."""

from __future__ import annotations

from typing import Any


def format_sft_text(example: dict[str, Any]) -> str:
    instruction = str(example.get("instruction", "")).strip()
    code = str(example.get("code", "")).strip()
    return (
        "### Instruction:\n"
        f"{instruction}\n\n"
        "### Response:\n"
        f"{code}"
    )


def build_sft_records(examples: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [{"text": format_sft_text(example)} for example in examples]
