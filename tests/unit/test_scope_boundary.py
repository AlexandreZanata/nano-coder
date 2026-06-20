"""Unit tests for scope boundary and BR-004 held-out leak detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_coder.domain.scope_boundary import (
    HeldOutLeakDetected,
    detect_held_out_leak,
    load_scope_boundary,
)
from nano_coder.domain.target_language import TargetLanguage

ROOT = Path(__file__).resolve().parents[2]
SCOPE_PATH = ROOT / "config" / "scope-boundary.yaml"


@pytest.fixture(scope="module")
def scope():
    return load_scope_boundary(SCOPE_PATH)


def test_scope_boundary_loads_150_held_out_topics(scope):
    assert len(scope.held_out_topics) == 150
    assert len(scope.training_topics) == 65
    assert scope.held_out_test_set_version == "held-out-v1"


def test_each_language_has_50_held_out_topics(scope):
    for language in TargetLanguage:
        assert len(scope.held_out_topics_for(language)) == 50


def test_training_and_held_out_topic_ids_disjoint(scope):
    assert scope.training_topic_ids.isdisjoint(scope.held_out_topic_ids)


def test_detect_leak_by_keyword(scope):
    with pytest.raises(HeldOutLeakDetected) as exc_info:
        detect_held_out_leak(
            scope,
            example_id="bad-seed-001",
            instruction="Build Express.js REST CRUD server with MongoDB",
            code="export function noop() {}",
            target_language=TargetLanguage.JAVASCRIPT,
        )
    assert exc_info.value.topic_id == "HO-JS-003"
    assert exc_info.value.matched_keyword == "express"


def test_other_language_held_out_keywords_ignored(scope):
    detect_held_out_leak(
        scope,
        example_id="REF-fmt-001",
        instruction="Document the expected model shape in a FreeMarker macro.",
        code="<#-- Model: products -->\n<#macro renderProductList products></#macro>",
        target_language=TargetLanguage.FREEMARKER,
    )


def test_detect_leak_by_topic_id(scope):
    with pytest.raises(HeldOutLeakDetected):
        detect_held_out_leak(
            scope,
            example_id="bad-seed-002",
            instruction="Simple utility",
            code="export const x = 1;",
            topic_id="HO-HTML-001",
        )


def test_clean_training_example_passes(scope):
    detect_held_out_leak(
        scope,
        example_id="seed-js-001",
        instruction="Write a function that groups objects by a key property.",
        code="export function groupBy(items, key) { return items.reduce((acc, item) => {"
        " const k = item[key]; (acc[k] ??= []).push(item); return acc; }, {}); }",
    )


def test_reference_seeds_pass_scope_check(scope):
    seeds_dir = ROOT / ".local" / "seeds" / "draft"
    if not seeds_dir.exists():
        pytest.skip("reference seeds not present")

    for path in seeds_dir.rglob("REF-*.json"):
        import json

        seed = json.loads(path.read_text(encoding="utf-8"))
        detect_held_out_leak(
            scope,
            example_id=seed["id"],
            instruction=seed["instruction"],
            code=seed["code"],
            target_language=TargetLanguage(seed["targetLanguage"]),
        )
