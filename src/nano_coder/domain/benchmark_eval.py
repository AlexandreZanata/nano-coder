"""Full held-out benchmark evaluation (UC-004, EVALUATION-METHOD.md)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_coder.domain.smoke_eval import evaluate_smoke_task
from nano_coder.domain.target_language import TargetLanguage

_HELD_OUT_FILES = {
    TargetLanguage.JAVASCRIPT: "js.jsonl",
    TargetLanguage.HTML: "html.jsonl",
    TargetLanguage.FREEMARKER: "fmt.jsonl",
}


class HeldOutVersionMismatch(Exception):
    """Requested test set version does not match manifest (BR-008)."""


@dataclass(frozen=True)
class LanguageBenchmarkSummary:
    language: TargetLanguage
    task_count: int
    pass_at_1: float
    pass_at_5: float
    syntax_validity_rate: float


@dataclass(frozen=True)
class BenchmarkSummary:
    held_out_test_set_version: str
    task_count: int
    pass_at_1: float
    pass_at_5: float
    syntax_validity_rate: float
    by_language: tuple[LanguageBenchmarkSummary, ...]


def load_held_out_manifest(held_out_root: Path) -> dict[str, Any]:
    path = held_out_root / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"held-out manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_test_set_version(
    held_out_root: Path,
    *,
    expected_version: str,
) -> dict[str, Any]:
    manifest = load_held_out_manifest(held_out_root)
    actual = manifest.get("heldOutTestSetVersion")
    if actual != expected_version:
        raise HeldOutVersionMismatch(
            f"expected held-out test set {expected_version}, found {actual}"
        )
    return manifest


def load_all_held_out_tasks(held_out_root: Path) -> dict[TargetLanguage, list[dict[str, Any]]]:
    tasks_by_language: dict[TargetLanguage, list[dict[str, Any]]] = {}
    for language, file_name in _HELD_OUT_FILES.items():
        path = held_out_root / file_name
        if not path.is_file():
            raise FileNotFoundError(f"held-out tasks not found: {path}")
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        tasks_by_language[language] = [json.loads(line) for line in lines if line.strip()]
    return tasks_by_language


def evaluate_task_pass_at_k(
    task: dict[str, Any],
    *,
    language: TargetLanguage,
    samples: list[str],
) -> tuple[bool, bool]:
    """Return (pass_at_1, pass_at_k) for generated samples."""
    results = [evaluate_smoke_task(task, sample, language=language) for sample in samples]
    pass_at_1 = results[0].passed if results else False
    pass_at_k = any(result.passed for result in results)
    return pass_at_1, pass_at_k


def summarize_language_benchmark(
    *,
    language: TargetLanguage,
    pass_at_1_hits: int,
    pass_at_k_hits: int,
    syntax_valid_hits: int,
    task_count: int,
) -> LanguageBenchmarkSummary:
    if task_count == 0:
        return LanguageBenchmarkSummary(
            language=language,
            task_count=0,
            pass_at_1=0.0,
            pass_at_5=0.0,
            syntax_validity_rate=0.0,
        )
    return LanguageBenchmarkSummary(
        language=language,
        task_count=task_count,
        pass_at_1=pass_at_1_hits / task_count,
        pass_at_5=pass_at_k_hits / task_count,
        syntax_validity_rate=syntax_valid_hits / task_count,
    )


def summarize_benchmark(
    summaries: list[LanguageBenchmarkSummary],
    *,
    held_out_test_set_version: str,
) -> BenchmarkSummary:
    task_count = sum(item.task_count for item in summaries)
    if task_count == 0:
        return BenchmarkSummary(
            held_out_test_set_version=held_out_test_set_version,
            task_count=0,
            pass_at_1=0.0,
            pass_at_5=0.0,
            syntax_validity_rate=0.0,
            by_language=tuple(summaries),
        )

    weighted_pass_at_1 = sum(item.pass_at_1 * item.task_count for item in summaries) / task_count
    weighted_pass_at_5 = sum(item.pass_at_5 * item.task_count for item in summaries) / task_count
    weighted_syntax = (
        sum(item.syntax_validity_rate * item.task_count for item in summaries) / task_count
    )
    return BenchmarkSummary(
        held_out_test_set_version=held_out_test_set_version,
        task_count=task_count,
        pass_at_1=weighted_pass_at_1,
        pass_at_5=weighted_pass_at_5,
        syntax_validity_rate=weighted_syntax,
        by_language=tuple(summaries),
    )
