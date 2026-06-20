"""Automated quality gates for synthetic examples (Stage 5, BR-002, BR-005, BR-010)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_coder.domain.gold_seed_example import SeedValidationError, validate_synthetic_example
from nano_coder.domain.quality_gates_config import QualityGatesConfig
from nano_coder.domain.rejection_reason import RejectionReasonCode
from nano_coder.domain.scope_boundary import (
    HeldOutLeakDetected,
    ScopeBoundary,
    detect_held_out_leak,
)
from nano_coder.domain.seed_promotion import instruction_similarity
from nano_coder.domain.seed_taxonomy import SeedTaxonomy
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.syntax_validators import (
    LintValidationError,
    SyntaxValidationError,
    validate_javascript_lint,
    validate_syntax,
)


@dataclass(frozen=True)
class GateDecision:
    example_id: str
    accepted: bool
    reason_code: RejectionReasonCode | None
    message: str | None
    gates_passed: tuple[str, ...]


def check_instruction_quality(instruction: str, config: QualityGatesConfig) -> str | None:
    lowered = instruction.lower().strip()
    if len(instruction) < config.instruction_min_length:
        return f"instruction shorter than {config.instruction_min_length} characters"

    for phrase in config.vague_phrases:
        if phrase in lowered:
            return f"instruction contains vague phrase '{phrase}'"

    words = set(lowered.replace("-", " ").split())
    if not words & config.imperative_verbs:
        return "instruction must start with an imperative verb (write, create, build, …)"

    return None


def _reject(
    example_id: str,
    reason_code: RejectionReasonCode,
    message: str,
    gates_passed: tuple[str, ...],
) -> GateDecision:
    return GateDecision(
        example_id=example_id,
        accepted=False,
        reason_code=reason_code,
        message=message,
        gates_passed=gates_passed,
    )


def _accept(example_id: str, gates_passed: tuple[str, ...]) -> GateDecision:
    return GateDecision(
        example_id=example_id,
        accepted=True,
        reason_code=None,
        message=None,
        gates_passed=gates_passed,
    )


def run_synthetic_gates(
    record: dict[str, Any],
    *,
    taxonomy: SeedTaxonomy,
    scope: ScopeBoundary,
    config: QualityGatesConfig,
    baseline_instructions: list[str],
    accepted_instructions: list[str],
    eslint_config: Path | None = None,
    skip_lint: bool = False,
) -> GateDecision:
    """Run sequential quality gates on one synthetic example (BR-002)."""
    example_id = str(record.get("id", "<unknown>"))
    passed: list[str] = []

    if config.schema_validation:
        try:
            validate_synthetic_example(record, taxonomy)
        except SeedValidationError as exc:
            return _reject(example_id, RejectionReasonCode.SCHEMA_INVALID, str(exc), tuple(passed))
        passed.append("SchemaValidation")

    language = TargetLanguage(record["targetLanguage"])
    instruction = record["instruction"]
    code = record["code"]

    if config.syntax_validation:
        try:
            validate_syntax(language, code)
        except SyntaxValidationError as exc:
            return _reject(example_id, RejectionReasonCode.SYNTAX_FAIL, exc.message, tuple(passed))
        passed.append("SyntaxValidation")

    if (
        config.lint_pass
        and language is TargetLanguage.JAVASCRIPT
        and eslint_config
        and not skip_lint
    ):
        try:
            validate_javascript_lint(code, eslint_config)
        except LintValidationError as exc:
            return _reject(example_id, RejectionReasonCode.LINT_FAIL, exc.message, tuple(passed))
        passed.append("LintPass")

    if config.instruction_quality:
        quality_error = check_instruction_quality(instruction, config)
        if quality_error:
            return _reject(
                example_id,
                RejectionReasonCode.QUALITY_BAR,
                quality_error,
                tuple(passed),
            )
        passed.append("InstructionQuality")

    if config.duplicate_check:
        for baseline in baseline_instructions + accepted_instructions:
            score = instruction_similarity(instruction, baseline)
            if score >= config.duplicate_similarity:
                return _reject(
                    example_id,
                    RejectionReasonCode.DUPLICATE,
                    f"instruction similarity {score:.2f} with prior example",
                    tuple(passed),
                )
        passed.append("DuplicateCheck")

    if config.held_out_leak:
        try:
            detect_held_out_leak(
                scope,
                example_id=example_id,
                instruction=instruction,
                code=code,
                target_language=language,
            )
        except HeldOutLeakDetected as exc:
            return _reject(example_id, RejectionReasonCode.HELD_OUT_LEAK, str(exc), tuple(passed))
        passed.append("HeldOutLeak")

    if config.llm_judge_enabled:
        score = record.get("judgeScore")
        if not isinstance(score, (int, float)) or score < config.llm_judge_min_score:
            if score is None:
                detail = "missing judgeScore"
            else:
                detail = f"judgeScore {score:.2f} below minimum"
            return _reject(example_id, RejectionReasonCode.LOW_JUDGE_SCORE, detail, tuple(passed))
        passed.append("LLMJudge")

    return _accept(example_id, tuple(passed))
