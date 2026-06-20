"""Unit tests for dataset publish validation (Stage 7)."""

from __future__ import annotations

import pytest

from nano_coder.domain.dataset_generation_run import DatasetGenerationState
from nano_coder.domain.dataset_publish import (
    DatasetPublishError,
    validate_dataset_version,
    validate_publish_preconditions,
    validate_version_language_alignment,
)
from nano_coder.domain.dataset_publish_config import load_dataset_publish_config
from nano_coder.domain.target_language import TargetLanguage

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def config():
    return load_dataset_publish_config(ROOT / "config" / "dataset-publish-v1.yaml")


def test_validate_dataset_version_accepts_canonical_format(config):
    validate_dataset_version("ds-2026-06-20-js-v1", config)


def test_validate_dataset_version_rejects_invalid_format(config):
    with pytest.raises(DatasetPublishError):
        validate_dataset_version("gen-js-smoke", config)


def test_validate_version_language_alignment(config):
    validate_version_language_alignment(
        "ds-2026-06-20-js-v1",
        TargetLanguage.JAVASCRIPT,
        config,
    )
    with pytest.raises(DatasetPublishError):
        validate_version_language_alignment(
            "ds-2026-06-20-html-v1",
            TargetLanguage.JAVASCRIPT,
            config,
        )


def test_validate_publish_preconditions_requires_completed_run(config):
    result = validate_publish_preconditions(
        filter_manifest={
            "targetLanguage": "JavaScript",
            "state": DatasetGenerationState.FILTERING.value,
            "syntaxPassRate": 0.95,
        },
        manual_review_manifest={
            "status": "Approved",
            "br005ManualReviewSatisfied": True,
        },
        accepted_count=1600,
        config=config,
    )
    assert not result.passed
    assert any("Completed" in failure for failure in result.failures)


def test_validate_publish_preconditions_enforces_br005_thresholds(config):
    result = validate_publish_preconditions(
        filter_manifest={
            "targetLanguage": "JavaScript",
            "state": DatasetGenerationState.COMPLETED.value,
            "syntaxPassRate": 0.80,
            "br005ManualReviewSatisfied": True,
        },
        manual_review_manifest={
            "status": "Approved",
            "br005ManualReviewSatisfied": True,
        },
        accepted_count=100,
        config=config,
    )
    assert not result.passed
    assert len(result.failures) >= 2


def test_validate_publish_preconditions_allows_skip_thresholds(config):
    result = validate_publish_preconditions(
        filter_manifest={
            "targetLanguage": "JavaScript",
            "state": DatasetGenerationState.COMPLETED.value,
            "syntaxPassRate": 0.80,
            "br005ManualReviewSatisfied": True,
        },
        manual_review_manifest={
            "status": "Approved",
            "br005ManualReviewSatisfied": True,
        },
        accepted_count=10,
        config=config,
        skip_thresholds=True,
    )
    assert result.passed
