"""Unit tests for FewShot baseline."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.fewshot_baseline import run_fewshot_baseline
from nano_coder.domain.compression_method import CompressionMethod
from nano_coder.domain.data_schedule import DataSchedule


def test_run_fewshot_baseline_writes_zero_param_checkpoint(tmp_path):
    result = run_fewshot_baseline(
        run_id="baseline-fewshot-smoke",
        dataset_version="ds-2026-06-20-mixed-v1",
        student_model="Qwen2.5-Coder-0.5B",
        data_schedule=DataSchedule.MIXED_LANGUAGES,
        checkpoint_root=tmp_path / "checkpoints",
        profile="smoke",
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["compressionMethod"] == CompressionMethod.FEW_SHOT.value
    assert manifest["trainableParamCount"] == 0
