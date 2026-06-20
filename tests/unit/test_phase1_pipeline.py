"""Unit tests for Phase 1 language pipeline (smoke profile)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from nano_coder.application.phase1_pipeline import Phase1Step, run_phase1_language_pipeline
from nano_coder.domain.phase1_config import load_phase1_config
from nano_coder.domain.target_language import TargetLanguage

ROOT = Path(__file__).resolve().parents[2]


def test_run_phase1_language_pipeline_smoke_profile(tmp_path, monkeypatch):
    base = load_phase1_config(ROOT / "config" / "phase1-v1.yaml")
    config = replace(
        base,
        target_count=10,
        dry_run_generation=True,
        skip_lint=True,
        skip_publish_thresholds=True,
        auto_approve_review=True,
        run_smoke_train=True,
    )

    published = tmp_path / "datasets"
    draft = tmp_path / "draft"
    raw = tmp_path / "raw"
    monkeypatch.setattr(
        "nano_coder.application.phase1_pipeline._resolve_paths",
        lambda _root: {
            "taxonomy": ROOT / "config" / "seeds-v1" / "taxonomy.yaml",
            "scope": ROOT / "config" / "scope-boundary.yaml",
            "gates": ROOT / "config" / "quality-gates-v1.yaml",
            "review_config": ROOT / "config" / "manual-review-v1.yaml",
            "publish_config": ROOT / "config" / "dataset-publish-v1.yaml",
            "smoke_config": ROOT / "config" / "smoke-train-v1.yaml",
            "generation": ROOT / "config" / "generation-v1.yaml",
            "prompts": ROOT / "config" / "prompts" / "v1",
            "seeds": ROOT / "data" / "seeds",
            "reference": ROOT / "data" / "seeds" / "reference",
            "raw": raw,
            "draft": draft,
            "rejected": tmp_path / "rejected.jsonl",
            "review_root": tmp_path / "review",
            "published": published,
            "events": tmp_path / "events.jsonl",
            "held_out": ROOT / "data" / "benchmarks" / "held-out-v1",
            "checkpoints": tmp_path / "checkpoints",
            "smoke_output": tmp_path / "smoke",
            "eslint": ROOT / "config" / "eslint" / "eslint.config.js",
            "phase1_log": tmp_path / "phase1",
        },
    )

    result = run_phase1_language_pipeline(
        language=TargetLanguage.JAVASCRIPT,
        config=config,
        project_root=ROOT,
        run_id="gen-js-phase1-test",
        dataset_version="ds-2026-06-20-js-v99",
        max_batches=2,
    )

    step_names = [step.step for step in result.steps]
    assert Phase1Step.GENERATE in step_names
    assert Phase1Step.FILTER in step_names
    assert Phase1Step.PUBLISH in step_names
    assert Phase1Step.SMOKE_TRAIN in step_names
    assert not result.failed
