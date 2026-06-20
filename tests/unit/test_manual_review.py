"""Unit tests for manual review domain logic (Stage 6)."""

from __future__ import annotations

import pytest

from nano_coder.domain.manual_review import (
    ManualReviewIncomplete,
    ManualReviewSampleRejected,
    ReviewDecision,
    compute_sample_size,
    evaluate_manual_review,
    select_review_sample,
)


def test_compute_sample_size_enforces_five_percent_minimum():
    assert compute_sample_size(100, sample_rate=0.05, min_sample_size=1) == 5
    assert compute_sample_size(10, sample_rate=0.05, min_sample_size=1) == 1
    assert compute_sample_size(0, sample_rate=0.05, min_sample_size=1) == 0


def test_select_review_sample_is_deterministic_for_run_id():
    records = [{"id": f"syn-js-{index:04d}"} for index in range(1, 21)]
    first = select_review_sample(
        records,
        run_id="gen-js-smoke",
        sample_rate=0.05,
        min_sample_size=1,
    )
    second = select_review_sample(
        records,
        run_id="gen-js-smoke",
        sample_rate=0.05,
        min_sample_size=1,
    )
    assert [record["id"] for record in first] == [record["id"] for record in second]
    assert len(first) == 1


def test_evaluate_manual_review_accepts_all_sample_decisions():
    outcome = evaluate_manual_review(
        ["syn-js-0001", "syn-js-0002"],
        {
            "syn-js-0001": ReviewDecision.ACCEPT,
            "syn-js-0002": ReviewDecision.ACCEPT,
        },
        accepted_count=40,
        sample_rate=0.05,
        require_all_sample_accepted=True,
    )
    assert outcome.approved
    assert outcome.br005_manual_review_satisfied


def test_evaluate_manual_review_requires_complete_decisions():
    with pytest.raises(ManualReviewIncomplete):
        evaluate_manual_review(
            ["syn-js-0001", "syn-js-0002"],
            {"syn-js-0001": ReviewDecision.ACCEPT},
            accepted_count=40,
            sample_rate=0.05,
            require_all_sample_accepted=True,
        )


def test_evaluate_manual_review_rejects_failed_sample():
    with pytest.raises(ManualReviewSampleRejected):
        evaluate_manual_review(
            ["syn-js-0001"],
            {"syn-js-0001": ReviewDecision.REJECT},
            accepted_count=20,
            sample_rate=0.05,
            require_all_sample_accepted=True,
        )
