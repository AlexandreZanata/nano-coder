"""Unit tests for GoldSeedExample validation (Stage 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nano_coder.domain.gold_seed_example import SeedValidationError, validate_gold_seed
from nano_coder.domain.scope_boundary import load_scope_boundary
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY_PATH = ROOT / "config" / "seeds-v1" / "taxonomy.yaml"
SCOPE_PATH = ROOT / "config" / "scope-boundary.yaml"
REFERENCE_DIR = ROOT / "data" / "seeds" / "reference"


@pytest.fixture(scope="module")
def taxonomy():
    return load_seed_taxonomy(TAXONOMY_PATH)


@pytest.fixture(scope="module")
def scope():
    return load_scope_boundary(SCOPE_PATH)


def test_reference_seeds_validate(taxonomy, scope):
    for path in sorted(REFERENCE_DIR.glob("REF-*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        validate_gold_seed(record, taxonomy, scope=scope, require_metadata=True)


def test_missing_difficulty_tag_fails(taxonomy):
    record = {
        "id": "seed-js-001",
        "targetLanguage": "JavaScript",
        "instruction": "Write a function that sums two numbers.",
        "code": "export function sum(a, b) { return a + b; }",
        "tags": ["array", "functional"],
    }
    with pytest.raises(SeedValidationError, match="difficulty"):
        validate_gold_seed(record, taxonomy, scope=None)


def test_invalid_id_prefix_fails(taxonomy):
    record = {
        "id": "seed-py-001",
        "targetLanguage": "JavaScript",
        "instruction": "Write a function that sums two numbers.",
        "code": "export function sum(a, b) { return a + b; }",
        "tags": ["array", "L2-standard"],
    }
    with pytest.raises(SeedValidationError, match="id"):
        validate_gold_seed(record, taxonomy, scope=None)


def test_domain_tag_required_for_language(taxonomy):
    record = {
        "id": "seed-html-001",
        "targetLanguage": "HTML",
        "instruction": "Write a semantic HTML5 article with header and footer.",
        "code": "<article><header></header><footer></footer></article>",
        "tags": ["L2-standard", "array"],
    }
    with pytest.raises(SeedValidationError, match="domain tag"):
        validate_gold_seed(record, taxonomy, scope=None)
