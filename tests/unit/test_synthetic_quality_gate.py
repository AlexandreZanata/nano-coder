"""Unit tests for synthetic quality gates (Stage 5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_coder.domain.gold_seed_example import SeedValidationError, validate_synthetic_example
from nano_coder.domain.quality_gates_config import load_quality_gates_config
from nano_coder.domain.rejection_reason import RejectionReasonCode
from nano_coder.domain.scope_boundary import load_scope_boundary
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy
from nano_coder.domain.synthetic_quality_gate import (
    check_instruction_quality,
    run_synthetic_gates,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def taxonomy():
    return load_seed_taxonomy(ROOT / "config" / "seeds-v1" / "taxonomy.yaml")


@pytest.fixture(scope="module")
def scope():
    return load_scope_boundary(ROOT / "config" / "scope-boundary.yaml")


@pytest.fixture(scope="module")
def gates_config():
    return load_quality_gates_config(ROOT / "config" / "quality-gates-v1.yaml")


def _valid_synthetic(index: int = 1) -> dict:
    return {
        "id": f"syn-js-{index:04d}",
        "targetLanguage": "JavaScript",
        "instruction": "Write a JavaScript function that sums numeric values in an array.",
        "code": (
            "/**\n * @param {number[]} values\n * @returns {number}\n */\n"
            "export function sumValues(values) {\n"
            "  return values.reduce((total, n) => total + n, 0);\n}\n"
        ),
        "tags": ["functional", "module", "L2-standard"],
        "metadata": {
            "author": "teacher-model",
            "created": "2026-06-20",
            "source": "synthetic",
        },
    }


def test_validate_synthetic_example_accepts_valid_record(taxonomy):
    validate_synthetic_example(_valid_synthetic(), taxonomy)


def test_validate_synthetic_example_rejects_gold_seed_id(taxonomy):
    record = _valid_synthetic()
    record["id"] = "seed-js-001"
    with pytest.raises(SeedValidationError):
        validate_synthetic_example(record, taxonomy)


def test_check_instruction_quality_rejects_vague_phrase(gates_config):
    error = check_instruction_quality("help me write something useful", gates_config)
    assert error is not None
    assert "vague" in error


def test_run_synthetic_gates_accepts_valid_example(taxonomy, scope, gates_config):
    decision = run_synthetic_gates(
        _valid_synthetic(),
        taxonomy=taxonomy,
        scope=scope,
        config=gates_config,
        baseline_instructions=[],
        accepted_instructions=[],
        skip_lint=True,
    )
    assert decision.accepted
    assert decision.reason_code is None
    assert "HeldOutLeak" in decision.gates_passed


def test_run_synthetic_gates_rejects_duplicate(taxonomy, scope, gates_config):
    record = _valid_synthetic()
    decision = run_synthetic_gates(
        record,
        taxonomy=taxonomy,
        scope=scope,
        config=gates_config,
        baseline_instructions=[],
        accepted_instructions=[record["instruction"]],
        skip_lint=True,
    )
    assert not decision.accepted
    assert decision.reason_code is RejectionReasonCode.DUPLICATE


def test_run_synthetic_gates_rejects_syntax_error(taxonomy, scope, gates_config):
    record = _valid_synthetic()
    record["code"] = "export function broken( { return 1; }\n"
    decision = run_synthetic_gates(
        record,
        taxonomy=taxonomy,
        scope=scope,
        config=gates_config,
        baseline_instructions=[],
        accepted_instructions=[],
        skip_lint=True,
    )
    assert not decision.accepted
    assert decision.reason_code is RejectionReasonCode.SYNTAX_FAIL
