"""Manual review sample selection and validation (Stage 6, BR-005)."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class ManualReviewStatus(StrEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class ReviewDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


class ManualReviewError(Exception):
    """Manual review workflow failed."""


class ManualReviewIncomplete(ManualReviewError):
    """Not every sampled example has an operator decision."""


class ManualReviewSampleRejected(ManualReviewError):
    """Operator rejected one or more sampled examples."""


@dataclass(frozen=True)
class ManualReviewOutcome:
    approved: bool
    sample_size: int
    accepted_count: int
    rejected_count: int
    br005_manual_review_satisfied: bool


def compute_sample_size(
    accepted_count: int,
    *,
    sample_rate: float,
    min_sample_size: int,
) -> int:
    if accepted_count <= 0:
        return 0
    target = max(min_sample_size, math.ceil(accepted_count * sample_rate))
    return min(accepted_count, target)


def _rng_for_run(run_id: str) -> random.Random:
    digest = hashlib.sha256(run_id.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def select_review_sample(
    records: list[dict[str, Any]],
    *,
    run_id: str,
    sample_rate: float,
    min_sample_size: int,
) -> list[dict[str, Any]]:
    """Deterministically sample examples for operator review (≥5% by default)."""
    size = compute_sample_size(
        len(records),
        sample_rate=sample_rate,
        min_sample_size=min_sample_size,
    )
    if size == 0:
        return []
    rng = _rng_for_run(run_id)
    return rng.sample(records, size)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")


def parse_decisions(raw: dict[str, Any]) -> dict[str, ReviewDecision]:
    decisions_raw = raw.get("decisions")
    if not isinstance(decisions_raw, dict):
        raise ManualReviewError("decisions file must contain a decisions object")

    parsed: dict[str, ReviewDecision] = {}
    for example_id, value in decisions_raw.items():
        if not isinstance(example_id, str) or not example_id.strip():
            raise ManualReviewError("decision keys must be non-empty example ids")
        if not isinstance(value, str):
            raise ManualReviewError(f"decision for {example_id} must be a string")
        try:
            parsed[example_id] = ReviewDecision(value.lower())
        except ValueError as exc:
            raise ManualReviewError(
                f"invalid decision '{value}' for {example_id}; use accept or reject"
            ) from exc
    return parsed


def evaluate_manual_review(
    sample_ids: list[str],
    decisions: dict[str, ReviewDecision],
    *,
    accepted_count: int,
    sample_rate: float,
    require_all_sample_accepted: bool,
) -> ManualReviewOutcome:
    missing = [example_id for example_id in sample_ids if example_id not in decisions]
    if missing:
        raise ManualReviewIncomplete(
            f"missing decisions for {len(missing)} sample example(s): {', '.join(missing[:5])}"
        )

    rejected = [
        example_id
        for example_id in sample_ids
        if decisions[example_id] is ReviewDecision.REJECT
    ]
    if require_all_sample_accepted and rejected:
        raise ManualReviewSampleRejected(
            f"operator rejected {len(rejected)} sample example(s): {', '.join(rejected[:5])}"
        )

    accepted_in_sample = len(sample_ids) - len(rejected)
    required_size = compute_sample_size(
        accepted_count,
        sample_rate=sample_rate,
        min_sample_size=1,
    )
    br005_satisfied = (
        len(sample_ids) >= required_size
        and accepted_in_sample == len(sample_ids)
        and require_all_sample_accepted
    )

    return ManualReviewOutcome(
        approved=len(rejected) == 0,
        sample_size=len(sample_ids),
        accepted_count=accepted_in_sample,
        rejected_count=len(rejected),
        br005_manual_review_satisfied=br005_satisfied,
    )
