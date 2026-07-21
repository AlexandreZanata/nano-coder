"""Unit tests for local gold-seed enterprise expansion."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_coder.domain.seed_promotion import instruction_similarity
from nano_coder.infrastructure.local_enterprise_expander import (
    expand_seed_record,
    vary_instruction,
)

ROOT = Path(__file__).resolve().parents[2]
JS_SEED = {
    "id": "seed-js-001",
    "targetLanguage": "JavaScript",
    "instruction": (
        "Write an ES module that exports `pluckNumbers`, which maps an array to its "
        "numeric elements only, preserving order."
    ),
    "code": "export function pluckNumbers(values) { return values; }\n",
    "tags": ["array", "functional", "L1-trivial"],
    "metadata": {"author": "test", "created": "2026-06-20", "source": "manual", "notes": "t"},
}


def test_vary_instruction_reduces_similarity_below_duplicate_threshold():
    base = JS_SEED["instruction"]
    for variant in range(14):
        varied = vary_instruction(base, variant)
        assert instruction_similarity(base, varied) < 0.95
        assert "todo" not in varied.lower()


def test_expand_seed_record_preserves_code_and_schema_fields():
    record = expand_seed_record(JS_SEED, variant=2, synthetic_id="syn-js-0001")
    assert record["id"] == "syn-js-0001"
    assert record["code"] == JS_SEED["code"]
    assert record["metadata"]["source"] == "synthetic"
    assert record["targetLanguage"] == "JavaScript"


@pytest.mark.parametrize(
    "camel_name",
    ["flattenToDotKeys", "pluckNumbers"],
)
def test_vary_instruction_avoids_todo_false_positive(camel_name: str):
    instruction = f"Write an ES module that exports `{camel_name}` for nested data."
    varied = vary_instruction(instruction, 1)
    assert "todo" not in varied.lower()
