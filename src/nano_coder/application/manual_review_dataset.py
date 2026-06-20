"""Application service — manual review sample queue (Stage 6, UC-001 step 8)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.dataset_generation_run import (
    DatasetGenerationRun,
    DatasetGenerationState,
)
from nano_coder.domain.manual_review import (
    ManualReviewError,
    ManualReviewOutcome,
    ManualReviewStatus,
    ReviewDecision,
    evaluate_manual_review,
    load_jsonl,
    select_review_sample,
    write_jsonl,
)
from nano_coder.domain.manual_review_config import ManualReviewConfig
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class PrepareReviewResult:
    run_id: str
    target_language: TargetLanguage
    accepted_count: int
    sample_size: int
    sample_path: Path
    queue_path: Path
    draft_dir: Path


@dataclass(frozen=True)
class SubmitReviewResult:
    run_id: str
    target_language: TargetLanguage
    outcome: ManualReviewOutcome
    manifest_path: Path
    final_state: DatasetGenerationState


def prepare_manual_review(
    *,
    run_id: str,
    draft_dir: Path,
    review_root: Path,
    config: ManualReviewConfig,
) -> PrepareReviewResult:
    accepted_path = draft_dir / "accepted.jsonl"
    if not accepted_path.is_file():
        raise ManualReviewError(f"accepted dataset not found: {accepted_path}")

    accepted_records = load_jsonl(accepted_path)
    if not accepted_records:
        raise ManualReviewError("cannot prepare manual review for empty accepted set")

    target_language = TargetLanguage(accepted_records[0]["targetLanguage"])
    sample_records = select_review_sample(
        accepted_records,
        run_id=run_id,
        sample_rate=config.sample_rate,
        min_sample_size=config.min_sample_size,
    )

    review_dir = review_root / run_id
    review_dir.mkdir(parents=True, exist_ok=True)
    sample_path = review_dir / "sample.jsonl"
    queue_path = review_dir / "review-queue.json"
    write_jsonl(sample_path, sample_records)

    queue = {
        "runId": run_id,
        "targetLanguage": target_language.value,
        "acceptedCount": len(accepted_records),
        "sampleRate": config.sample_rate,
        "sampleSize": len(sample_records),
        "sampleExampleIds": [record["id"] for record in sample_records],
        "status": ManualReviewStatus.PENDING.value,
        "createdAt": datetime.now(UTC).isoformat(),
        "configVersion": config.version,
        "reviewCriteria": list(config.review_criteria),
        "samplePath": str(sample_path),
    }
    queue_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")

    draft_queue_path = draft_dir / "review-queue.json"
    draft_queue_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    _update_filter_manifest_state(
        draft_dir,
        state=DatasetGenerationState.AWAITING_MANUAL_REVIEW,
        extra={"manualReviewSampleSize": len(sample_records)},
    )

    return PrepareReviewResult(
        run_id=run_id,
        target_language=target_language,
        accepted_count=len(accepted_records),
        sample_size=len(sample_records),
        sample_path=sample_path,
        queue_path=queue_path,
        draft_dir=draft_dir,
    )


def submit_manual_review(
    *,
    run_id: str,
    draft_dir: Path,
    review_root: Path,
    config: ManualReviewConfig,
    decisions: dict[str, ReviewDecision],
    reviewed_by: str,
) -> SubmitReviewResult:
    queue_path = review_root / run_id / "review-queue.json"
    if not queue_path.is_file():
        queue_path = draft_dir / "review-queue.json"
    if not queue_path.is_file():
        raise ManualReviewError(f"review queue not found for run {run_id}")

    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    if queue.get("status") != ManualReviewStatus.PENDING.value:
        raise ManualReviewError(f"review queue is not pending: {queue.get('status')}")

    sample_ids = queue["sampleExampleIds"]
    accepted_count = int(queue["acceptedCount"])
    target_language = TargetLanguage(queue["targetLanguage"])

    outcome = evaluate_manual_review(
        sample_ids,
        decisions,
        accepted_count=accepted_count,
        sample_rate=config.sample_rate,
        require_all_sample_accepted=config.require_all_sample_accepted,
    )

    run = DatasetGenerationRun(run_id, target_language.value)
    run.state = DatasetGenerationState.AWAITING_MANUAL_REVIEW
    final_state = (
        DatasetGenerationState.COMPLETED
        if outcome.approved
        else DatasetGenerationState.FAILED
    )
    run.transition(final_state)

    reviewed_at = datetime.now(UTC).isoformat()
    manifest = {
        "runId": run_id,
        "targetLanguage": target_language.value,
        "status": (
            ManualReviewStatus.APPROVED.value
            if outcome.approved
            else ManualReviewStatus.REJECTED.value
        ),
        "sampleSize": outcome.sample_size,
        "acceptedInSample": outcome.accepted_count,
        "rejectedInSample": outcome.rejected_count,
        "sampleRate": config.sample_rate,
        "reviewedBy": reviewed_by,
        "reviewedAt": reviewed_at,
        "br005ManualReviewSatisfied": outcome.br005_manual_review_satisfied,
        "decisions": {
            example_id: decisions[example_id].value for example_id in sample_ids
        },
        "finalState": final_state.value,
    }
    manifest_path = draft_dir / "manual-review-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    queue["status"] = manifest["status"]
    queue["reviewedAt"] = reviewed_at
    queue["reviewedBy"] = reviewed_by
    queue_path.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    draft_queue = draft_dir / "review-queue.json"
    if draft_queue != queue_path:
        draft_queue.write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")

    _update_filter_manifest_state(
        draft_dir,
        state=final_state,
        extra={
            "manualReviewStatus": manifest["status"],
            "br005ManualReviewSatisfied": outcome.br005_manual_review_satisfied,
        },
    )

    return SubmitReviewResult(
        run_id=run_id,
        target_language=target_language,
        outcome=outcome,
        manifest_path=manifest_path,
        final_state=final_state,
    )


def build_auto_accept_decisions(sample_ids: list[str]) -> dict[str, ReviewDecision]:
    return {example_id: ReviewDecision.ACCEPT for example_id in sample_ids}


def _update_filter_manifest_state(
    draft_dir: Path,
    *,
    state: DatasetGenerationState,
    extra: dict[str, Any] | None = None,
) -> None:
    manifest_path = draft_dir / "filter-manifest.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["state"] = state.value
    if extra:
        manifest.update(extra)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
