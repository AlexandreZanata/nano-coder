"""Unit tests for synthetic filter application (Stage 5)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.filter_synthetic import filter_synthetic_run, load_raw_candidates
from nano_coder.domain.quality_gates_config import load_quality_gates_config
from nano_coder.domain.scope_boundary import load_scope_boundary
from nano_coder.domain.seed_taxonomy import load_seed_taxonomy
from nano_coder.domain.target_language import TargetLanguage

ROOT = Path(__file__).resolve().parents[2]


def _write_batch(raw_dir: Path, records: list[dict]) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    (raw_dir / "batch-001.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_load_raw_candidates_reads_jsonl_batches(tmp_path):
    raw_dir = tmp_path / "gen-js-smoke"
    record = {"id": "syn-js-0001", "targetLanguage": "JavaScript"}
    _write_batch(raw_dir, [record])
    loaded = load_raw_candidates(raw_dir)
    assert len(loaded) == 1
    assert loaded[0]["id"] == "syn-js-0001"


def test_filter_synthetic_run_writes_accepted_and_rejected(tmp_path):
    raw_dir = tmp_path / "raw" / "gen-js-smoke"
    good = {
        "id": "syn-js-0001",
        "targetLanguage": "JavaScript",
        "instruction": "Write a JavaScript function that counts items in an array.",
        "code": "export function countItems(items) { return items.length; }\n",
        "tags": ["array", "functional", "L2-standard"],
        "metadata": {
            "author": "teacher-model",
            "created": "2026-06-20",
            "source": "synthetic",
        },
    }
    bad = dict(good)
    bad["id"] = "syn-js-0002"
    bad["instruction"] = "help me fix this array counter please now"
    _write_batch(raw_dir, [good, bad])

    output_root = tmp_path / "draft"
    rejected_log = tmp_path / "rejected.jsonl"
    result = filter_synthetic_run(
        raw_dir=raw_dir,
        output_root=output_root,
        rejected_log=rejected_log,
        taxonomy=load_seed_taxonomy(ROOT / "config" / "seeds-v1" / "taxonomy.yaml"),
        scope=load_scope_boundary(ROOT / "config" / "scope-boundary.yaml"),
        config=load_quality_gates_config(ROOT / "config" / "quality-gates-v1.yaml"),
        seeds_root=ROOT / "data" / "seeds",
        skip_lint=True,
        language=TargetLanguage.JAVASCRIPT,
    )

    assert result.candidate_count == 2
    assert result.accepted_count == 1
    assert result.rejected_count == 1
    assert (result.output_dir / "accepted.jsonl").is_file()
    assert (result.output_dir / "rejected.jsonl").is_file()
    assert (result.output_dir / "filter-manifest.json").is_file()
    assert result.syntax_pass_rate == 1.0
    assert "QUALITY_BAR" in result.rejections_by_reason
