"""Phase 4 evaluation configuration (EVALUATION-METHOD.md)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class EvaluationSettings:
    include_tag_buckets: bool
    include_inference_metrics: bool
    include_param_match_footnotes: bool
    judge_sample_rate: float


@dataclass(frozen=True)
class InferenceMockSettings:
    mean_latency_ms_per_token: float
    throughput_tokens_per_sec: float
    base_model_size_mb: float


@dataclass(frozen=True)
class Phase4Config:
    version: str
    held_out_test_set_version: str
    profile: str
    anchor_compression_method: str
    param_match_tolerance_percent: float
    evaluation: EvaluationSettings
    inference_mock: InferenceMockSettings
    phase3_report: str
    smoke_train_report: str


def load_phase4_config(path: Path) -> Phase4Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    evaluation = raw["evaluation"]
    inference = raw["inferenceMock"]
    sources = raw["sources"]
    return Phase4Config(
        version=raw["version"],
        held_out_test_set_version=str(defaults["heldOutTestSetVersion"]),
        profile=str(defaults["profile"]),
        anchor_compression_method=str(defaults["anchorCompressionMethod"]),
        param_match_tolerance_percent=float(defaults["paramMatchTolerancePercent"]),
        evaluation=EvaluationSettings(
            include_tag_buckets=bool(evaluation["includeTagBuckets"]),
            include_inference_metrics=bool(evaluation["includeInferenceMetrics"]),
            include_param_match_footnotes=bool(evaluation["includeParamMatchFootnotes"]),
            judge_sample_rate=float(evaluation["judgeSampleRate"]),
        ),
        inference_mock=InferenceMockSettings(
            mean_latency_ms_per_token=float(inference["meanLatencyMsPerToken"]),
            throughput_tokens_per_sec=float(inference["throughputTokensPerSec"]),
            base_model_size_mb=float(inference["baseModelSizeMb"]),
        ),
        phase3_report=str(sources["phase3Report"]),
        smoke_train_report=str(sources["smokeTrainReport"]),
    )
