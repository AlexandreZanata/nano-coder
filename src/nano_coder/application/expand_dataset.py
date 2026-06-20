"""Application service — teacher expansion loop (UC-001, Stage 4)."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from nano_coder.domain.budget_guard import BudgetExceeded, BudgetGuard, SeedCountInsufficient, TokenPricing
from nano_coder.domain.dataset_generation_run import DatasetGenerationRun, DatasetGenerationState
from nano_coder.domain.expansion_method import ExpansionMethod
from nano_coder.domain.scope_boundary import ScopeBoundary, load_scope_boundary
from nano_coder.domain.seed_promotion import language_dir_name, load_seed_records
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.domain.teacher_response import TeacherClient, extract_json_object
from nano_coder.infrastructure.prompt_renderer import PromptRenderer

_METHOD_SEQUENCE = (
    ExpansionMethod.SELF_INSTRUCT,
    ExpansionMethod.SELF_INSTRUCT,
    ExpansionMethod.SELF_INSTRUCT,
    ExpansionMethod.EVOL_DEEPEN,
    ExpansionMethod.EVOL_WIDEN,
    ExpansionMethod.EVOL_SHORTEN,
)


@dataclass
class ExpansionConfig:
    target_count: int
    batch_size: int
    max_budget_usd: float
    min_gold_seeds: int
    prompt_version: str
    model: str
    max_tokens: int
    pricing: TokenPricing


@dataclass
class ExpansionResult:
    run_id: str
    target_language: TargetLanguage
    candidate_count: int
    batch_count: int
    spent_usd: float
    output_dir: Path
    failed: bool
    failure_reason: str | None = None


@dataclass
class _RunContext:
    run: DatasetGenerationRun
    language: TargetLanguage
    seeds: list[dict[str, Any]]
    reference_seeds: list[dict[str, Any]]
    output_dir: Path
    renderer: PromptRenderer
    scope: ScopeBoundary
    config: ExpansionConfig
    budget: BudgetGuard
    teacher: TeacherClient
    candidates: list[dict[str, Any]] = field(default_factory=list)
    batch_index: int = 0
    events: list[dict[str, Any]] = field(default_factory=list)


def load_expansion_config(path: Path) -> ExpansionConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    pricing_raw = raw["pricingUsdPerMillionTokens"]
    defaults = raw["defaults"]
    teacher = raw["teacher"]
    return ExpansionConfig(
        target_count=int(defaults["targetCount"]),
        batch_size=int(defaults["batchSize"]),
        max_budget_usd=float(defaults["maxBudgetUsd"]),
        min_gold_seeds=int(defaults["minGoldSeeds"]),
        prompt_version=raw["promptVersion"],
        model=teacher["model"],
        max_tokens=int(teacher["maxTokens"]),
        pricing=TokenPricing(
            input_usd_per_million=float(pricing_raw["input"]),
            output_usd_per_million=float(pricing_raw["output"]),
        ),
    )


def _load_gold_seeds(seeds_root: Path, language: TargetLanguage) -> list[dict[str, Any]]:
    folder = seeds_root / language_dir_name(language)
    return load_seed_records(folder)


def _held_out_summary(scope: ScopeBoundary, language: TargetLanguage) -> str:
    topics = scope.held_out_topics_for(language)[:8]
    lines = [f"- {topic.pattern}" for topic in topics]
    return "\n".join(lines) + "\n- (and 42 more held-out patterns — see config/scope-boundary.yaml)"


def _out_of_scope_summary(scope: ScopeBoundary, language: TargetLanguage) -> str:
    return "\n".join(f"- {item}" for item in scope.out_of_scope_phase1[language])


def _pick_few_shots(ctx: _RunContext, count: int = 5) -> list[dict[str, Any]]:
    refs = ctx.reference_seeds[:3]
    pool = [seed for seed in ctx.seeds if seed not in refs]
    extra = random.sample(pool, k=min(2, len(pool)))
    return refs + extra


def _select_method(batch_index: int) -> ExpansionMethod:
    return _METHOD_SEQUENCE[batch_index % len(_METHOD_SEQUENCE)]


def _build_prompts(
    ctx: _RunContext,
    method: ExpansionMethod,
    *,
    batch_index: int,
) -> tuple[str, str]:
    lang = ctx.language
    prefix = PromptRenderer.lang_prefix(lang)
    system_template = ctx.renderer.load("self-instruct-system.md")
    system = ctx.renderer.render(
        system_template,
        {
            "OUT_OF_SCOPE": _out_of_scope_summary(ctx.scope, lang),
            "HELD_OUT_SUMMARY": _held_out_summary(ctx.scope, lang),
        },
    )

    if method is ExpansionMethod.SELF_INSTRUCT:
        few_shots = _pick_few_shots(ctx)
        lang_topics = [topic for topic in ctx.scope.training_topics if topic.language is lang]
        domain_tag = lang_topics[batch_index % len(lang_topics)].tags[0] if lang_topics else "functional"
        user_template = ctx.renderer.load("self-instruct-user.md")
        user = ctx.renderer.render(
            user_template,
            {
                "TARGET_LANGUAGE": lang.value,
                "DIFFICULTY_TARGET": "L2-standard",
                "DOMAIN_TAG": domain_tag,
                "FEW_SHOT_SEEDS": PromptRenderer.format_few_shot_seeds(few_shots),
                "LANG_PREFIX": prefix,
            },
        )
        return system, user

    base = ctx.seeds[batch_index % len(ctx.seeds)]
    base_json = json.dumps(base, indent=2, ensure_ascii=False)
    template_name = {
        ExpansionMethod.EVOL_DEEPEN: "evol-instruct-deepen.md",
        ExpansionMethod.EVOL_WIDEN: "evol-instruct-widen.md",
        ExpansionMethod.EVOL_SHORTEN: "evol-instruct-shorten.md",
    }[method]
    user_template = ctx.renderer.load(template_name)
    values = {
        "TARGET_LANGUAGE": lang.value,
        "BASE_SEED_ID": base["id"],
        "BASE_SEED_JSON": base_json,
        "LANG_PREFIX": prefix,
        "FROM_LEVEL": "2",
        "TO_LEVEL": "3",
        "DOMAIN_TAG": base.get("tags", ["functional"])[0],
        "DIFFICULTY": "L2-standard",
    }
    return system, ctx.renderer.render(user_template, values)


def _append_event(ctx: _RunContext, event_type: str, payload: dict[str, Any]) -> None:
    ctx.events.append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "runId": ctx.run.run_id,
            "event": event_type,
            **payload,
        }
    )


def _write_batch(ctx: _RunContext, batch_records: list[dict[str, Any]]) -> None:
    ctx.batch_index += 1
    batch_path = ctx.output_dir / f"batch-{ctx.batch_index:03d}.jsonl"
    lines = [json.dumps(record, ensure_ascii=False) for record in batch_records]
    batch_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _append_event(
        ctx,
        "BatchWritten",
        {"batchId": batch_path.name, "count": len(batch_records)},
    )


def run_expansion(
    *,
    run_id: str,
    language: TargetLanguage,
    seeds_root: Path,
    reference_root: Path,
    prompt_dir: Path,
    scope_path: Path,
    output_root: Path,
    config: ExpansionConfig,
    teacher: TeacherClient,
    target_count: int | None = None,
    max_batches: int | None = None,
) -> ExpansionResult:
    gold_seeds = _load_gold_seeds(seeds_root, language)
    if len(gold_seeds) < config.min_gold_seeds:
        raise SeedCountInsufficient(language.value, len(gold_seeds), config.min_gold_seeds)

    reference_seeds = load_seed_records(reference_root)
    scope = load_scope_boundary(scope_path)
    renderer = PromptRenderer(prompt_dir)
    budget = BudgetGuard(max_budget_usd=config.max_budget_usd, pricing=config.pricing)

    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    run = DatasetGenerationRun(run_id, language.value)
    run.transition(DatasetGenerationState.GENERATING)

    ctx = _RunContext(
        run=run,
        language=language,
        seeds=gold_seeds,
        reference_seeds=reference_seeds,
        output_dir=output_dir,
        renderer=renderer,
        scope=scope,
        config=config,
        budget=budget,
        teacher=teacher,
    )

    goal = target_count or config.target_count
    batches_run = 0
    failure_reason: str | None = None
    failed = False

    _append_event(ctx, "DatasetGenerationStarted", {"targetCount": goal, "language": language.value})

    while len(ctx.candidates) < goal:
        if max_batches is not None and batches_run >= max_batches:
            break

        method = _select_method(batches_run)
        system, user = _build_prompts(ctx, method, batch_index=batches_run)
        batch_records: list[dict[str, Any]] = []

        for _ in range(config.batch_size):
            if len(ctx.candidates) >= goal:
                break
            try:
                response = teacher.complete(system=system, user=user)
                cost = ctx.budget.record(response.input_tokens, response.output_tokens)
                record = extract_json_object(response.text)
                record.setdefault("targetLanguage", language.value)
                record.setdefault(
                    "metadata",
                    {
                        "author": "teacher-model",
                        "created": datetime.now(UTC).date().isoformat(),
                        "source": "synthetic",
                    },
                )
                batch_records.append(record)
                ctx.candidates.append(record)
                _append_event(
                    ctx,
                    "SyntheticExampleGenerated",
                    {
                        "exampleId": record.get("id"),
                        "method": method.value,
                        "inputTokens": response.input_tokens,
                        "outputTokens": response.output_tokens,
                        "costUsd": round(cost, 6),
                        "model": response.model,
                    },
                )
            except BudgetExceeded as exc:
                failed = True
                failure_reason = str(exc)
                run.transition(DatasetGenerationState.FAILED)
                break
            except (ValueError, json.JSONDecodeError, KeyError) as exc:
                _append_event(ctx, "ExampleRejected", {"reason": str(exc), "method": method.value})
                continue

        if batch_records:
            _write_batch(ctx, batch_records)
        batches_run += 1
        if failed:
            break

    if not failed:
        run.transition(DatasetGenerationState.FILTERING)

    manifest = {
        "runId": run_id,
        "targetLanguage": language.value,
        "promptVersion": config.prompt_version,
        "teacherModel": config.model,
        "candidateCount": len(ctx.candidates),
        "batchCount": ctx.batch_index,
        "targetCount": goal,
        "spentUsd": round(ctx.budget.spent_usd, 4),
        "inputTokens": ctx.budget.input_tokens,
        "outputTokens": ctx.budget.output_tokens,
        "state": run.state.value,
        "failed": failed,
        "failureReason": failure_reason,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    log_path = output_dir / "run-log.jsonl"
    log_path.write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in ctx.events) + "\n",
        encoding="utf-8",
    )

    return ExpansionResult(
        run_id=run_id,
        target_language=language,
        candidate_count=len(ctx.candidates),
        batch_count=ctx.batch_index,
        spent_usd=ctx.budget.spent_usd,
        output_dir=output_dir,
        failed=failed,
        failure_reason=failure_reason,
    )
