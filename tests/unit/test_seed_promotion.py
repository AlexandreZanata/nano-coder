"""Unit tests for seed promotion gates (Stage 3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_coder.domain.scope_boundary import load_scope_boundary
from nano_coder.domain.seed_promotion import (
    find_duplicate_pairs,
    instruction_similarity,
    load_seed_records,
    run_promotion_gates,
)
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy
from nano_coder.infrastructure.syntax_validators import (
    SyntaxValidationError,
    validate_freemarker_syntax,
    validate_html_syntax,
    validate_javascript_syntax,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def taxonomy():
    return load_seed_taxonomy(ROOT / "config" / "seeds-v1" / "taxonomy.yaml")


@pytest.fixture(scope="module")
def scope():
    return load_scope_boundary(ROOT / "config" / "scope-boundary.yaml")


def test_instruction_similarity_detects_near_duplicates():
    left = "Write a function that groups objects by a key property in JavaScript"
    right = "Write a function that groups objects by key property in JavaScript"
    assert instruction_similarity(left, right) >= 0.9


def test_find_duplicate_pairs_returns_empty_for_distinct_seeds(taxonomy, scope):
    records = load_seed_records(ROOT / "data" / "seeds" / "javascript")[:5]
    assert find_duplicate_pairs(records) == []


def test_javascript_syntax_accepts_valid_module():
    code = "export function sum(a, b) { return a + b; }\n"
    validate_javascript_syntax(code)


def test_html_syntax_rejects_missing_root():
    with pytest.raises(SyntaxValidationError):
        validate_html_syntax("<div>hello</div>")


def test_freemarker_syntax_rejects_unclosed_macro():
    with pytest.raises(SyntaxValidationError):
        validate_freemarker_syntax("<#macro greet name>Hello ${name?html}")


def test_promotion_gates_pass_for_javascript_seeds(taxonomy, scope):
    records = load_seed_records(ROOT / "data" / "seeds" / "javascript")
    result = run_promotion_gates(
        records,
        taxonomy=taxonomy,
        scope=scope,
        eslint_config=None,
        skip_lint=True,
    )
    assert result.passed, result.failures
