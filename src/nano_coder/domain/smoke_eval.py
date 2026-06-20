"""Smoke evaluation for held-out tasks (Stage 8, ADR-002, EVALUATION-METHOD.md)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_coder.domain.manual_review import load_jsonl
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.infrastructure.syntax_validators import SyntaxValidationError, validate_syntax

_HELD_OUT_FILES = {
    TargetLanguage.JAVASCRIPT: "js.jsonl",
    TargetLanguage.HTML: "html.jsonl",
    TargetLanguage.FREEMARKER: "fmt.jsonl",
}


@dataclass(frozen=True)
class SmokeTaskResult:
    task_id: str
    passed: bool
    reason: str | None


@dataclass(frozen=True)
class SmokeEvalSummary:
    task_count: int
    passed_count: int
    pass_at_1: float
    gate_satisfied: bool
    results: tuple[SmokeTaskResult, ...]


def load_held_out_tasks(
    held_out_root: Path,
    language: TargetLanguage,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    file_name = _HELD_OUT_FILES[language]
    path = held_out_root / file_name
    if not path.is_file():
        raise FileNotFoundError(f"held-out tasks not found: {path}")
    tasks = load_jsonl(path)
    return tasks[:limit]


def evaluate_smoke_task(
    task: dict[str, Any],
    generated_code: str,
    *,
    language: TargetLanguage,
) -> SmokeTaskResult:
    task_id = str(task.get("id", "<unknown>"))
    criteria = task.get("acceptanceCriteria") or {}

    if criteria.get("mustParse"):
        try:
            validate_syntax(language, generated_code)
        except SyntaxValidationError as exc:
            return SmokeTaskResult(task_id, False, f"syntax: {exc.message}")

    lowered = generated_code.lower()
    for keyword in criteria.get("mustContain", []):
        if str(keyword).lower() not in lowered:
            return SmokeTaskResult(task_id, False, f"missing keyword: {keyword}")

    for keyword in criteria.get("mustNotContain", []):
        if str(keyword).lower() in lowered:
            return SmokeTaskResult(task_id, False, f"forbidden keyword: {keyword}")

    return SmokeTaskResult(task_id, True, None)


def summarize_smoke_eval(
    results: list[SmokeTaskResult],
    *,
    min_pass_at_1: float,
) -> SmokeEvalSummary:
    passed_count = sum(1 for result in results if result.passed)
    task_count = len(results)
    pass_at_1 = passed_count / task_count if task_count else 0.0
    return SmokeEvalSummary(
        task_count=task_count,
        passed_count=passed_count,
        pass_at_1=pass_at_1,
        gate_satisfied=pass_at_1 >= min_pass_at_1,
        results=tuple(results),
    )
