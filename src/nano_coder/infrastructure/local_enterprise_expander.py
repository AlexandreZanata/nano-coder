"""Expand gold seeds into enterprise synthetic examples without TeacherModel API."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from nano_coder.domain.seed_promotion import language_dir_name, load_seed_records
from nano_coder.domain.target_language import TargetLanguage

_LANG_SYN_PREFIX = {
    TargetLanguage.JAVASCRIPT: "js",
    TargetLanguage.HTML: "html",
    TargetLanguage.FREEMARKER: "fmt",
}

_SAFE_IMPERATIVES = (
    "Write",
    "Create",
    "Build",
    "Implement",
    "Develop",
    "Design",
    "Construct",
    "Produce",
)

_ENTERPRISE_CONTEXTS = (
    "enterprise billing modules",
    "customer self-service portals",
    "internal admin dashboards",
    "audit-ready compliance tooling",
    "operations control consoles",
    "finance reporting workflows",
    "inventory management systems",
    "subscription lifecycle services",
    "identity verification flows",
    "document approval pipelines",
    "multi-tenant SaaS backends",
    "regulated healthcare portals",
    "retail checkout experiences",
    "logistics tracking consoles",
)

_INSTRUCTION_PREFIXES = (
    "Write ",
    "Create ",
    "Build ",
    "Implement ",
    "Develop ",
    "Define ",
    "Design ",
    "Render ",
    "Add ",
)


def _decamelize(name: str) -> str:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return spaced.replace("_", " ").lower()


def _sanitize_backtick_exports(instruction: str) -> str:
    """Replace backtick export names with spaced words (avoids vague 'todo' false positives)."""

    def replace(match: re.Match[str]) -> str:
        return _decamelize(match.group(1))

    return re.sub(r"`([^`]+)`", replace, instruction)


def _strip_leading_imperative(instruction: str) -> str:
    stripped = instruction.strip()
    for prefix in _INSTRUCTION_PREFIXES:
        if stripped.startswith(prefix):
            return stripped[len(prefix):]
    return stripped


def vary_instruction(base_instruction: str, variant: int) -> str:
    """Produce a distinct imperative instruction for the same underlying task."""
    imperative = _SAFE_IMPERATIVES[variant % len(_SAFE_IMPERATIVES)]
    context = _ENTERPRISE_CONTEXTS[variant % len(_ENTERPRISE_CONTEXTS)]
    core = _sanitize_backtick_exports(_strip_leading_imperative(base_instruction))
    family = variant % 3
    if family == 0:
        return f"{imperative} a production-grade module for {context} that {core}"
    if family == 1:
        return f"{imperative} enterprise code for {context}: {core}"
    return f"For {context}, {imperative.lower()} an implementation where {core}"


def expand_seed_record(seed: dict[str, Any], *, variant: int, synthetic_id: str) -> dict[str, Any]:
    record = {
        "id": synthetic_id,
        "targetLanguage": seed["targetLanguage"],
        "instruction": vary_instruction(seed["instruction"], variant),
        "code": seed["code"],
        "tags": list(seed["tags"]),
        "metadata": {
            "author": "agent-expander",
            "created": date.today().isoformat(),
            "source": "synthetic",
            "notes": f"local-expansion: seed={seed['id']} variant={variant}",
        },
    }
    return record


def expand_language_seeds(
    seeds: list[dict[str, Any]],
    language: TargetLanguage,
    *,
    variants_per_seed: int,
) -> list[dict[str, Any]]:
    prefix = _LANG_SYN_PREFIX[language]
    candidates: list[dict[str, Any]] = []
    for seed_index, seed in enumerate(seeds):
        for variant in range(variants_per_seed):
            serial = seed_index * variants_per_seed + variant + 1
            synthetic_id = f"syn-{prefix}-{serial:04d}"
            candidates.append(expand_seed_record(seed, variant=variant, synthetic_id=synthetic_id))
    return candidates


def load_gold_seeds(seeds_root: Path, language: TargetLanguage) -> list[dict[str, Any]]:
    folder = seeds_root / language_dir_name(language)
    return load_seed_records(folder)


def write_raw_batches(
    candidates: list[dict[str, Any]],
    output_dir: Path,
    *,
    batch_size: int = 25,
    run_id: str,
    language: TargetLanguage,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_index = 0
    for offset in range(0, len(candidates), batch_size):
        batch_index += 1
        chunk = candidates[offset : offset + batch_size]
        batch_path = output_dir / f"batch-{batch_index:03d}.jsonl"
        batch_path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in chunk) + "\n",
            encoding="utf-8",
        )

    manifest = {
        "runId": run_id,
        "targetLanguage": language.value,
        "promptVersion": "local-agent-v1",
        "teacherModel": "agent-expander",
        "candidateCount": len(candidates),
        "batchCount": batch_index,
        "targetCount": len(candidates),
        "spentUsd": 0.0,
        "inputTokens": 0,
        "outputTokens": 0,
        "state": "Filtering",
        "failed": False,
        "failureReason": None,
        "expansionMethod": "local-gold-seed-variation",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def generate_local_enterprise_raw(
    *,
    language: TargetLanguage,
    run_id: str,
    seeds_root: Path,
    output_root: Path,
    variants_per_seed: int = 14,
    batch_size: int = 25,
) -> tuple[Path, int]:
    seeds = load_gold_seeds(seeds_root, language)
    candidates = expand_language_seeds(seeds, language, variants_per_seed=variants_per_seed)
    output_dir = output_root / run_id
    write_raw_batches(
        candidates,
        output_dir,
        batch_size=batch_size,
        run_id=run_id,
        language=language,
    )
    return output_dir, len(candidates)
