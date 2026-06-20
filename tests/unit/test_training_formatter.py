"""Unit tests for SFT formatting."""

from __future__ import annotations

from nano_coder.infrastructure.training_formatter import build_sft_records, format_sft_text


def test_format_sft_text_includes_instruction_and_code() -> None:
    text = format_sft_text({"instruction": "Write a function", "code": "export function f() {}"})
    assert "### Instruction:" in text
    assert "Write a function" in text
    assert "### Response:" in text
    assert "export function f() {}" in text


def test_build_sft_records_wraps_text_field() -> None:
    records = build_sft_records([{"instruction": "a", "code": "b"}])
    assert records == [{"text": format_sft_text({"instruction": "a", "code": "b"})}]
