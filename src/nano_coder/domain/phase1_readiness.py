"""Phase 1 readiness checks (operator playbook Part 1.3)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from nano_coder.domain.phase1_config import Phase1Config
from nano_coder.domain.published_dataset import DatasetNotPublishedError, load_published_dataset
from nano_coder.domain.seed_promotion import language_dir_name, load_seed_records
from nano_coder.domain.synthetic_dataset import SyntheticDatasetState
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Phase1ReadinessResult:
    passed: bool
    checks: tuple[ReadinessCheck, ...]


def verify_phase1_readiness(
    *,
    seeds_root: Path,
    published_root: Path,
    config: Phase1Config,
    dataset_versions: dict[TargetLanguage, str] | None = None,
) -> Phase1ReadinessResult:
    checks: list[ReadinessCheck] = []

    for language in TargetLanguage:
        folder = seeds_root / language_dir_name(language)
        count = len(load_seed_records(folder)) if folder.is_dir() else 0
        passed = count >= config.required_seeds_per_language
        checks.append(
            ReadinessCheck(
                name=f"BR-001 seeds {language.value}",
                passed=passed,
                detail=f"{count}/{config.required_seeds_per_language} gold seeds",
            )
        )

    index_path = published_root / "published-index.json"
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        checks.append(
            ReadinessCheck(
                name="published-index.json",
                passed=True,
                detail=f"{len(index)} published version(s) indexed",
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                name="published-index.json",
                passed=False,
                detail="index file missing",
            )
        )

    if dataset_versions is not None:
        for language in config.required_published_languages:
            version = dataset_versions.get(language)
            if version is None:
                checks.append(
                    ReadinessCheck(
                        name=f"published dataset {language.value}",
                        passed=False,
                        detail="version not provided",
                    )
                )
                continue
            try:
                dataset = load_published_dataset(published_root, version)
                lang_ok = dataset.target_language is language
                state_ok = dataset.manifest.get("state") == SyntheticDatasetState.PUBLISHED.value
                passed = lang_ok and state_ok
                checks.append(
                    ReadinessCheck(
                        name=f"published dataset {language.value}",
                        passed=passed,
                        detail=f"{version} — {dataset.example_count} examples",
                    )
                )
            except DatasetNotPublishedError as exc:
                checks.append(
                    ReadinessCheck(
                        name=f"published dataset {language.value}",
                        passed=False,
                        detail=str(exc),
                    )
                )

    return Phase1ReadinessResult(
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )
