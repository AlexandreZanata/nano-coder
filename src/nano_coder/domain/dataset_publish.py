"""Dataset publish validation and version rules (Stage 7, BR-005, BR-007)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nano_coder.domain.dataset_generation_run import DatasetGenerationState
from nano_coder.domain.dataset_publish_config import DatasetPublishConfig
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState
from nano_coder.domain.target_language import TargetLanguage

_VERSION_LANG = {
    "js": TargetLanguage.JAVASCRIPT,
    "html": TargetLanguage.HTML,
    "fmt": TargetLanguage.FREEMARKER,
}


class DatasetPublishError(Exception):
    """Dataset publish preconditions failed."""


@dataclass(frozen=True)
class PublishValidationResult:
    passed: bool
    accepted_count: int
    syntax_pass_rate: float
    manual_review_satisfied: bool
    run_state: str
    target_language: TargetLanguage
    failures: tuple[str, ...]


def validate_dataset_version(version: str, config: DatasetPublishConfig) -> None:
    if not config.dataset_version_pattern.match(version):
        raise DatasetPublishError(
            "dataset version must match ds-YYYY-MM-DD-(js|html|fmt|mixed)-vN"
        )


def validate_version_language_alignment(
    version: str,
    language: TargetLanguage,
    config: DatasetPublishConfig,
) -> None:
    validate_dataset_version(version, config)
    match = config.dataset_version_pattern.match(version)
    assert match is not None
    code = match.group(1)
    if code == "mixed":
        return
    expected = _VERSION_LANG[code]
    if language is not expected:
        raise DatasetPublishError(
            f"dataset version suffix '{code}' does not match language {language.value}"
        )


def validate_publish_preconditions(
    *,
    filter_manifest: dict[str, Any],
    manual_review_manifest: dict[str, Any] | None,
    accepted_count: int,
    config: DatasetPublishConfig,
    skip_thresholds: bool = False,
) -> PublishValidationResult:
    failures: list[str] = []
    target_language = TargetLanguage(filter_manifest["targetLanguage"])
    run_state = str(filter_manifest.get("state", ""))
    syntax_pass_rate = float(filter_manifest.get("syntaxPassRate", 0.0))
    manual_review_satisfied = bool(
        filter_manifest.get("br005ManualReviewSatisfied", False)
        or (manual_review_manifest or {}).get("br005ManualReviewSatisfied", False)
    )

    if config.require_run_completed and run_state != DatasetGenerationState.COMPLETED.value:
        failures.append(
            f"run state must be {DatasetGenerationState.COMPLETED.value}, got {run_state}"
        )

    if manual_review_manifest is None:
        failures.append("manual-review-manifest.json is required")
    elif manual_review_manifest.get("status") != "Approved":
        failures.append("manual review sample was not approved")

    if config.require_manual_review and not manual_review_satisfied:
        failures.append("manual review BR-005 threshold not satisfied")

    if not skip_thresholds:
        if accepted_count < config.min_accepted_per_language:
            failures.append(
                f"accepted count {accepted_count} below minimum "
                f"{config.min_accepted_per_language}"
            )
        if syntax_pass_rate < config.min_syntax_pass_rate:
            failures.append(
                f"syntax pass rate {syntax_pass_rate:.2%} below minimum "
                f"{config.min_syntax_pass_rate:.0%}"
            )

    return PublishValidationResult(
        passed=len(failures) == 0,
        accepted_count=accepted_count,
        syntax_pass_rate=syntax_pass_rate,
        manual_review_satisfied=manual_review_satisfied,
        run_state=run_state,
        target_language=target_language,
        failures=tuple(failures),
    )


def build_published_manifest(
    *,
    dataset_version: str,
    draft_id: str,
    target_language: TargetLanguage,
    example_count: int,
    syntax_pass_rate: float,
    published_by: str,
    published_at: str,
    source_filter_manifest: dict[str, Any],
    source_manual_review_manifest: dict[str, Any],
    br005_satisfied: bool,
) -> dict[str, Any]:
    return {
        "datasetVersion": dataset_version,
        "draftId": draft_id,
        "state": SyntheticDatasetState.PUBLISHED.value,
        "targetLanguage": target_language.value,
        "exampleCount": example_count,
        "syntaxPassRate": round(syntax_pass_rate, 4),
        "publishedAt": published_at,
        "publishedBy": published_by,
        "sourceRunId": draft_id,
        "br005Satisfied": br005_satisfied,
        "filterManifestSnapshot": {
            "runId": source_filter_manifest.get("runId"),
            "filteredAt": source_filter_manifest.get("filteredAt"),
            "gatesConfigVersion": source_filter_manifest.get("gatesConfigVersion"),
        },
        "manualReviewSnapshot": {
            "reviewedBy": source_manual_review_manifest.get("reviewedBy"),
            "reviewedAt": source_manual_review_manifest.get("reviewedAt"),
            "sampleSize": source_manual_review_manifest.get("sampleSize"),
        },
    }


def build_dataset_published_event(
    *,
    dataset_version: str,
    draft_id: str,
    target_language: TargetLanguage,
    example_count: int,
    published_by: str,
    published_at: str,
) -> dict[str, Any]:
    return {
        "event": "DatasetPublished",
        "timestamp": published_at,
        "datasetVersion": dataset_version,
        "draftId": draft_id,
        "targetLanguage": target_language.value,
        "exampleCount": example_count,
        "publishedBy": published_by,
    }
