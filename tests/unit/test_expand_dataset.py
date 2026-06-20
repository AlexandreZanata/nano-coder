"""Unit tests for Stage 4 teacher expansion."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nano_coder.application.expand_dataset import load_expansion_config, run_expansion
from nano_coder.domain.budget_guard import BudgetExceeded, BudgetGuard, TokenPricing
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.domain.teacher_response import extract_json_object
from nano_coder.infrastructure.teacher_client import MockTeacherClient

ROOT = Path(__file__).resolve().parents[2]


def test_extract_json_object_strips_fences():
    raw = '```json\n{"id": "syn-js-0001", "code": "export const x = 1;"}\n```'
    parsed = extract_json_object(raw)
    assert parsed["id"] == "syn-js-0001"


def test_budget_guard_raises_when_exceeded():
    guard = BudgetGuard(max_budget_usd=0.001, pricing=TokenPricing(3.0, 15.0))
    with pytest.raises(BudgetExceeded):
        guard.record(input_tokens=500, output_tokens=500)


def test_dry_run_expansion_writes_batches(tmp_path):
    config = load_expansion_config(ROOT / "config" / "generation-v1.yaml")
    config = config.__class__(
        target_count=10,
        batch_size=5,
        max_budget_usd=config.max_budget_usd,
        min_gold_seeds=config.min_gold_seeds,
        prompt_version=config.prompt_version,
        model=config.model,
        max_tokens=config.max_tokens,
        pricing=config.pricing,
    )
    result = run_expansion(
        run_id="test-run",
        language=TargetLanguage.JAVASCRIPT,
        seeds_root=ROOT / "data" / "seeds",
        reference_root=ROOT / "data" / "seeds" / "reference",
        prompt_dir=ROOT / "config" / "prompts" / "v1",
        scope_path=ROOT / "config" / "scope-boundary.yaml",
        output_root=tmp_path,
        config=config,
        teacher=MockTeacherClient(TargetLanguage.JAVASCRIPT),
        target_count=10,
        max_batches=2,
    )
    assert result.candidate_count == 10
    assert result.batch_count == 2
    manifest = json.loads((tmp_path / "test-run" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["candidateCount"] == 10
    assert (tmp_path / "test-run" / "batch-001.jsonl").is_file()
