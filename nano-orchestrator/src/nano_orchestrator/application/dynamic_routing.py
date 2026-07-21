"""Load Phase 5 dynamic worker routing from config (bake-off scores)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nano_orchestrator.application.worker_dispatch import WorkerRouting
from nano_orchestrator.domain.entities import TargetLanguage

DEFAULT_ROUTING_CONFIG = (
    Path(__file__).resolve().parents[3] / "config" / "worker_routing.json"
)


@dataclass(frozen=True, slots=True)
class DebateConfig:
    enabled: bool = False
    acceptance_token: str = "critical"


@dataclass(frozen=True, slots=True)
class RetryThresholds:
    max_budget: int = 2
    high_confidence_min: float = 0.8
    medium_confidence_min: float = 0.5


@dataclass(frozen=True, slots=True)
class DynamicRoutingConfig:
    routing: WorkerRouting
    debate: DebateConfig
    retry: RetryThresholds
    prefer_fine_tuned: bool
    scores: dict[str, list[dict[str, Any]]]
    source_path: Path


def select_best_model(
    candidates: list[dict[str, Any]],
    *,
    fallback: str,
) -> str:
    """Pick highest pass_at_1; tie-break on lower p50_ms."""
    if not candidates:
        return fallback
    ranked = sorted(
        candidates,
        key=lambda row: (-float(row.get("pass_at_1", 0.0)), float(row.get("p50_ms", 1e9))),
    )
    model_id = ranked[0].get("model_id")
    return str(model_id) if model_id else fallback


def build_routing_from_scores(
    scores: dict[str, list[dict[str, Any]]],
    *,
    fallback: str,
    prefer_fine_tuned: bool,
    fine_tuned_overrides: dict[str, str] | None = None,
) -> WorkerRouting:
    overrides = fine_tuned_overrides or {}
    picks: dict[str, str] = {}
    for lang in ("javascript", "html", "freemarker", "css"):
        if prefer_fine_tuned and overrides.get(lang):
            picks[lang] = overrides[lang]
        else:
            # CSS shares HTML bake-off scores when css scores are absent
            score_key = lang if scores.get(lang) else ("html" if lang == "css" else lang)
            picks[lang] = select_best_model(scores.get(score_key, []), fallback=fallback)
    return WorkerRouting(
        javascript=picks["javascript"],
        html=picks["html"],
        freemarker=picks["freemarker"],
        css=picks["css"],
        default=fallback,
    )


def load_dynamic_routing(
    path: Path | None = None,
) -> DynamicRoutingConfig:
    config_path = path or DEFAULT_ROUTING_CONFIG
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    scores = dict(payload.get("scores") or {})
    fallback = str(payload.get("fallback_model_id") or "qwen25-coder-0.5b")
    prefer_ft = bool(payload.get("prefer_fine_tuned", True))
    overrides = {
        str(k): str(v) for k, v in dict(payload.get("fine_tuned_overrides") or {}).items()
    }
    routing = build_routing_from_scores(
        scores,
        fallback=fallback,
        prefer_fine_tuned=prefer_ft,
        fine_tuned_overrides=overrides,
    )
    debate_raw = dict(payload.get("debate") or {})
    retry_raw = dict(payload.get("retry") or {})
    return DynamicRoutingConfig(
        routing=routing,
        debate=DebateConfig(
            enabled=bool(debate_raw.get("enabled", False)),
            acceptance_token=str(debate_raw.get("acceptance_token") or "critical"),
        ),
        retry=RetryThresholds(
            max_budget=int(retry_raw.get("max_budget", 2)),
            high_confidence_min=float(retry_raw.get("high_confidence_min", 0.8)),
            medium_confidence_min=float(retry_raw.get("medium_confidence_min", 0.5)),
        ),
        prefer_fine_tuned=prefer_ft,
        scores=scores,
        source_path=config_path,
    )


def model_for_language(routing: WorkerRouting, language: TargetLanguage) -> str:
    return routing.model_for(language)
