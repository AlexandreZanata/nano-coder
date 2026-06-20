"""Seed promotion gates and duplicate detection (Stage 3, BR-001, BR-003, BR-004)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from nano_coder.domain.gold_seed_example import SeedValidationError, validate_gold_seed
from nano_coder.domain.scope_boundary import HeldOutLeakDetected, ScopeBoundary, detect_held_out_leak
from nano_coder.domain.seed_taxonomy import SeedTaxonomy
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.syntax_validators import (
    LintValidationError,
    SyntaxValidationError,
    validate_javascript_lint,
    validate_syntax,
)

_LANG_DIRS = {
    TargetLanguage.JAVASCRIPT: "javascript",
    TargetLanguage.HTML: "html",
    TargetLanguage.FREEMARKER: "freemarker",
}


class QualityGateType(StrEnum):
    SCHEMA = "SchemaValidation"
    SYNTAX = "SyntaxValidation"
    LINT = "LintPass"
    HELD_OUT = "HeldOutLeak"
    DUPLICATE = "DuplicateCheck"


@dataclass(frozen=True)
class GateFailure:
    seed_id: str
    gate: QualityGateType
    message: str


@dataclass(frozen=True)
class PromotionResult:
    passed: bool
    seed_count: int
    failures: tuple[GateFailure, ...]
    counts_by_language: dict[str, int]


def language_dir_name(language: TargetLanguage) -> str:
    return _LANG_DIRS[language]


def load_seed_records(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        return [json.loads(path.read_text(encoding="utf-8"))]
    records: list[dict[str, Any]] = []
    for file in sorted(path.rglob("*.json")):
        if file.name.startswith("REF-"):
            continue
        records.append(json.loads(file.read_text(encoding="utf-8")))
    return records


def _normalize_instruction(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def instruction_similarity(left: str, right: str) -> float:
    """Jaccard similarity on normalized instruction tokens."""
    a = _normalize_instruction(left)
    b = _normalize_instruction(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_duplicate_pairs(
    records: list[dict[str, Any]],
    *,
    threshold: float = 0.95,
) -> list[tuple[str, str, float]]:
    pairs: list[tuple[str, str, float]] = []
    for i, left in enumerate(records):
        for right in records[i + 1 :]:
            if left.get("targetLanguage") != right.get("targetLanguage"):
                continue
            score = instruction_similarity(left.get("instruction", ""), right.get("instruction", ""))
            if score >= threshold:
                pairs.append((left["id"], right["id"], score))
    return pairs


def run_promotion_gates(
    records: list[dict[str, Any]],
    *,
    taxonomy: SeedTaxonomy,
    scope: ScopeBoundary,
    eslint_config: Path | None = None,
    duplicate_threshold: float = 0.95,
    skip_lint: bool = False,
) -> PromotionResult:
    failures: list[GateFailure] = []

    for record in records:
        seed_id = record.get("id", "<unknown>")

        try:
            validate_gold_seed(record, taxonomy, scope=scope, require_metadata=True)
        except SeedValidationError as exc:
            failures.append(GateFailure(seed_id, QualityGateType.SCHEMA, str(exc)))
            continue

        language = TargetLanguage(record["targetLanguage"])
        code = record["code"]

        try:
            validate_syntax(language, code)
        except SyntaxValidationError as exc:
            failures.append(GateFailure(seed_id, QualityGateType.SYNTAX, exc.message))

        if language is TargetLanguage.JAVASCRIPT and eslint_config and not skip_lint:
            try:
                validate_javascript_lint(code, eslint_config)
            except LintValidationError as exc:
                failures.append(GateFailure(seed_id, QualityGateType.LINT, exc.message))

        try:
            detect_held_out_leak(
                scope,
                example_id=seed_id,
                instruction=record["instruction"],
                code=code,
                target_language=language,
            )
        except HeldOutLeakDetected as exc:
            failures.append(GateFailure(seed_id, QualityGateType.HELD_OUT, str(exc)))

    for left_id, right_id, score in find_duplicate_pairs(records, threshold=duplicate_threshold):
        failures.append(
            GateFailure(
                left_id,
                QualityGateType.DUPLICATE,
                f"instruction similarity {score:.2f} with {right_id}",
            )
        )

    counts: dict[str, int] = {lang.value: 0 for lang in TargetLanguage}
    for record in records:
        counts[record["targetLanguage"]] += 1

    return PromotionResult(
        passed=len(failures) == 0,
        seed_count=len(records),
        failures=tuple(failures),
        counts_by_language=counts,
    )


def write_promoted_seeds(records: list[dict[str, Any]], output_root: Path) -> None:
    for record in records:
        language = TargetLanguage(record["targetLanguage"])
        folder = output_root / language_dir_name(language)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{record['id']}.json"
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_manifest(
    result: PromotionResult,
    *,
    seed_set_version: str,
    scope_version: str,
    taxonomy_version: str,
    gates_run: list[str],
) -> dict[str, Any]:
    return {
        "seedSetVersion": seed_set_version,
        "scopeBoundaryVersion": scope_version,
        "taxonomyVersion": taxonomy_version,
        "promotedAt": _today_iso(),
        "gatesRun": gates_run,
        "seedCount": result.seed_count,
        "countsByLanguage": result.counts_by_language,
        "br001Satisfied": all(count >= 50 for count in result.counts_by_language.values()),
        "passed": result.passed,
    }


def _today_iso() -> str:
    from datetime import date

    return date.today().isoformat()
