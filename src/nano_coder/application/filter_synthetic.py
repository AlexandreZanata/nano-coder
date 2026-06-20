"""Application service — filter raw synthetic batches through quality gates (Stage 5)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nano_coder.domain.quality_gates_config import QualityGatesConfig
from nano_coder.domain.scope_boundary import ScopeBoundary
from nano_coder.domain.seed_promotion import language_dir_name, load_seed_records
from nano_coder.domain.seed_taxonomy import SeedTaxonomy
from nano_coder.domain.synthetic_quality_gate import GateDecision, run_synthetic_gates
from nano_coder.domain.target_language import TargetLanguage


@dataclass(frozen=True)
class FilterResult:
    run_id: str
    target_language: TargetLanguage
    candidate_count: int
    accepted_count: int
    rejected_count: int
    syntax_pass_count: int
    syntax_pass_rate: float
    rejections_by_reason: dict[str, int]
    output_dir: Path
    br005_syntax_satisfied: bool
    br005_count_satisfied: bool


@dataclass
class _FilterStats:
    syntax_pass_count: int = 0
    rejections_by_reason: dict[str, int] = field(default_factory=dict)


def load_raw_candidates(raw_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for batch_path in sorted(raw_dir.glob("batch-*.jsonl")):
        for line in batch_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def _baseline_instructions(seeds_root: Path, language: TargetLanguage) -> list[str]:
    folder = seeds_root / language_dir_name(language)
    if not folder.is_dir():
        return []
    return [record["instruction"] for record in load_seed_records(folder)]


def _infer_language(
    records: list[dict[str, Any]],
    fallback: TargetLanguage | None,
) -> TargetLanguage:
    if records:
        return TargetLanguage(records[0]["targetLanguage"])
    if fallback is not None:
        return fallback
    raise ValueError("cannot infer target language from empty candidate set")


def _append_rejected_log(path: Path, entries: list[dict[str, Any]]) -> None:
    if not entries:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, ensure_ascii=False) for entry in entries]
    with path.open("a", encoding="utf-8") as handle:
        if path.stat().st_size > 0:
            handle.write("\n")
        handle.write("\n".join(lines) + "\n")


def filter_synthetic_run(
    *,
    raw_dir: Path,
    output_root: Path,
    rejected_log: Path,
    taxonomy: SeedTaxonomy,
    scope: ScopeBoundary,
    config: QualityGatesConfig,
    seeds_root: Path,
    eslint_config: Path | None = None,
    skip_lint: bool = False,
    language: TargetLanguage | None = None,
) -> FilterResult:
    run_id = raw_dir.name
    candidates = load_raw_candidates(raw_dir)
    target_language = _infer_language(candidates, language)

    baseline = _baseline_instructions(seeds_root, target_language)
    accepted_records: list[dict[str, Any]] = []
    rejected_records: list[dict[str, Any]] = []
    accepted_instructions: list[str] = []
    stats = _FilterStats()

    for record in candidates:
        decision = run_synthetic_gates(
            record,
            taxonomy=taxonomy,
            scope=scope,
            config=config,
            baseline_instructions=baseline,
            accepted_instructions=accepted_instructions,
            eslint_config=eslint_config,
            skip_lint=skip_lint,
        )
        _track_syntax(decision, stats)
        if decision.accepted:
            accepted_records.append(record)
            accepted_instructions.append(record["instruction"])
        else:
            rejected_records.append(_rejection_entry(record, decision))

    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "accepted.jsonl", accepted_records)
    _write_jsonl(output_dir / "rejected.jsonl", rejected_records)
    _append_rejected_log(rejected_log, rejected_records)

    syntax_total = len(candidates)
    syntax_rate = stats.syntax_pass_count / syntax_total if syntax_total else 0.0
    manifest = {
        "runId": run_id,
        "targetLanguage": target_language.value,
        "filteredAt": datetime.now(UTC).isoformat(),
        "candidateCount": len(candidates),
        "acceptedCount": len(accepted_records),
        "rejectedCount": len(rejected_records),
        "syntaxPassCount": stats.syntax_pass_count,
        "syntaxPassRate": round(syntax_rate, 4),
        "rejectionsByReason": stats.rejections_by_reason,
        "gatesConfigVersion": config.version,
        "br005SyntaxSatisfied": syntax_rate >= config.min_syntax_pass_rate,
        "br005CountSatisfied": len(accepted_records) >= config.min_accepted_per_language,
    }
    (output_dir / "filter-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    return FilterResult(
        run_id=run_id,
        target_language=target_language,
        candidate_count=len(candidates),
        accepted_count=len(accepted_records),
        rejected_count=len(rejected_records),
        syntax_pass_count=stats.syntax_pass_count,
        syntax_pass_rate=syntax_rate,
        rejections_by_reason=stats.rejections_by_reason,
        output_dir=output_dir,
        br005_syntax_satisfied=manifest["br005SyntaxSatisfied"],
        br005_count_satisfied=manifest["br005CountSatisfied"],
    )


def _track_syntax(decision: GateDecision, stats: _FilterStats) -> None:
    if "SyntaxValidation" in decision.gates_passed:
        stats.syntax_pass_count += 1

    if decision.reason_code is not None:
        key = decision.reason_code.value
        stats.rejections_by_reason[key] = stats.rejections_by_reason.get(key, 0) + 1


def _rejection_entry(record: dict[str, Any], decision: GateDecision) -> dict[str, Any]:
    return {
        "example": record,
        "exampleId": decision.example_id,
        "reasonCode": decision.reason_code.value if decision.reason_code else None,
        "message": decision.message,
        "gatesPassed": list(decision.gates_passed),
        "rejectedAt": datetime.now(UTC).isoformat(),
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text(("\n".join(lines) + "\n") if lines else "", encoding="utf-8")
