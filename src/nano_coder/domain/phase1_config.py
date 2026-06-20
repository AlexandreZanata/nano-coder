"""Phase 1 operator pipeline configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class Phase1Config:
    version: str
    target_count: int
    wave: int
    date_stamp: str
    operator_id: str
    dry_run_generation: bool
    skip_lint: bool
    skip_publish_thresholds: bool
    auto_approve_review: bool
    run_smoke_train: bool
    language_codes: dict[TargetLanguage, str]
    run_id_template: str
    version_template: str
    mixed_version_template: str
    required_seeds_per_language: int
    required_published_languages: tuple[TargetLanguage, ...]


def load_phase1_config(path: Path) -> Phase1Config:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw["defaults"]
    language_codes = {
        TargetLanguage(name): code for name, code in raw["languageCodes"].items()
    }
    return Phase1Config(
        version=raw["version"],
        target_count=int(defaults["targetCount"]),
        wave=int(defaults["wave"]),
        date_stamp=str(defaults["dateStamp"]),
        operator_id=str(defaults["operatorId"]),
        dry_run_generation=bool(defaults["dryRunGeneration"]),
        skip_lint=bool(defaults["skipLint"]),
        skip_publish_thresholds=bool(defaults["skipPublishThresholds"]),
        auto_approve_review=bool(defaults["autoApproveReview"]),
        run_smoke_train=bool(defaults["runSmokeTrain"]),
        language_codes=language_codes,
        run_id_template=str(raw["runIdTemplate"]),
        version_template=str(raw["versionTemplate"]),
        mixed_version_template=str(raw["mixedVersionTemplate"]),
        required_seeds_per_language=int(raw["requiredSeedsPerLanguage"]),
        required_published_languages=tuple(
            TargetLanguage(name) for name in raw["requiredPublishedLanguages"]
        ),
    )


def format_run_id(config: Phase1Config, language: TargetLanguage) -> str:
    lang_code = config.language_codes[language]
    return config.run_id_template.format(
        lang=lang_code,
        wave=config.wave,
        date=config.date_stamp,
    )


def format_dataset_version(config: Phase1Config, language: TargetLanguage) -> str:
    lang_code = config.language_codes[language]
    return config.version_template.format(
        lang=lang_code,
        wave=config.wave,
        date=config.date_stamp,
    )


def format_mixed_version(config: Phase1Config) -> str:
    return config.mixed_version_template.format(
        wave=config.wave,
        date=config.date_stamp,
    )
