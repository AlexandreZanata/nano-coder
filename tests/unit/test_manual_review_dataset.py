"""Unit tests for manual review application service (Stage 6)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.manual_review_dataset import (
    prepare_manual_review,
    submit_manual_review,
)
from nano_coder.domain.dataset_generation_run import DatasetGenerationState
from nano_coder.domain.manual_review import ReviewDecision
from nano_coder.domain.manual_review_config import load_manual_review_config

ROOT = Path(__file__).resolve().parents[2]


def _write_accepted(path: Path, count: int) -> None:
    lines = []
    for index in range(1, count + 1):
        record = {
            "id": f"syn-js-{index:04d}",
            "targetLanguage": "JavaScript",
            "instruction": f"Write a JavaScript helper #{index}.",
            "code": f"export function helper{index}() {{ return {index}; }}\n",
            "tags": ["functional", "module", "L2-standard"],
            "metadata": {
                "author": "teacher-model",
                "created": "2026-06-20",
                "source": "synthetic",
            },
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_prepare_and_submit_manual_review_flow(tmp_path):
    run_id = "gen-js-smoke"
    draft_dir = tmp_path / "draft" / run_id
    draft_dir.mkdir(parents=True)
    _write_accepted(draft_dir / "accepted.jsonl", 20)
    (draft_dir / "filter-manifest.json").write_text(
        json.dumps({"runId": run_id, "state": "Filtering"}) + "\n",
        encoding="utf-8",
    )

    config = load_manual_review_config(ROOT / "config" / "manual-review-v1.yaml")
    review_root = tmp_path / "review"

    prepared = prepare_manual_review(
        run_id=run_id,
        draft_dir=draft_dir,
        review_root=review_root,
        config=config,
    )
    assert prepared.sample_size == 1
    assert prepared.sample_path.is_file()
    assert (draft_dir / "review-queue.json").is_file()

    filter_manifest = json.loads((draft_dir / "filter-manifest.json").read_text(encoding="utf-8"))
    assert filter_manifest["state"] == DatasetGenerationState.AWAITING_MANUAL_REVIEW.value

    queue = json.loads((prepared.queue_path).read_text(encoding="utf-8"))
    decisions = {
        example_id: ReviewDecision.ACCEPT for example_id in queue["sampleExampleIds"]
    }
    submitted = submit_manual_review(
        run_id=run_id,
        draft_dir=draft_dir,
        review_root=review_root,
        config=config,
        decisions=decisions,
        reviewed_by="operator",
    )

    assert submitted.final_state is DatasetGenerationState.COMPLETED
    assert submitted.outcome.br005_manual_review_satisfied
    assert (draft_dir / "manual-review-manifest.json").is_file()

    final_manifest = json.loads((draft_dir / "filter-manifest.json").read_text(encoding="utf-8"))
    assert final_manifest["state"] == DatasetGenerationState.COMPLETED.value
    assert final_manifest["br005ManualReviewSatisfied"] is True
