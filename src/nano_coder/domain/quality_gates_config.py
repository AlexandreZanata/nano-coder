"""Quality gate configuration for synthetic filtering (Stage 5)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class QualityGatesConfig:
    version: str
    schema_validation: bool
    syntax_validation: bool
    lint_pass: bool
    instruction_quality: bool
    duplicate_check: bool
    held_out_leak: bool
    llm_judge_enabled: bool
    llm_judge_min_score: float
    duplicate_similarity: float
    instruction_min_length: int
    imperative_verbs: frozenset[str]
    vague_phrases: frozenset[str]
    min_accepted_per_language: int
    min_syntax_pass_rate: float


def load_quality_gates_config(path: Path) -> QualityGatesConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    gates = raw["gates"]
    thresholds = raw["thresholds"]
    llm_judge = gates["llmJudge"]
    publish = raw["publishDefaults"]
    return QualityGatesConfig(
        version=raw["version"],
        schema_validation=bool(gates["schemaValidation"]),
        syntax_validation=bool(gates["syntaxValidation"]),
        lint_pass=bool(gates["lintPass"]),
        instruction_quality=bool(gates["instructionQuality"]),
        duplicate_check=bool(gates["duplicateCheck"]),
        held_out_leak=bool(gates["heldOutLeak"]),
        llm_judge_enabled=bool(llm_judge["enabled"]),
        llm_judge_min_score=float(llm_judge["minScore"]),
        duplicate_similarity=float(thresholds["duplicateSimilarity"]),
        instruction_min_length=int(thresholds["instructionMinLength"]),
        imperative_verbs=frozenset(str(v).lower() for v in raw["imperativeVerbs"]),
        vague_phrases=frozenset(str(v).lower() for v in raw["vaguePhrases"]),
        min_accepted_per_language=int(publish["minAcceptedPerLanguage"]),
        min_syntax_pass_rate=float(publish["minSyntaxPassRate"]),
    )
