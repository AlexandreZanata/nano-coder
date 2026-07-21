"""Append-only structured LLM call log (ASI02 — observability)."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_LOG = _DEFAULT_ROOT / "logs" / "llm_calls.jsonl"


def default_log_path() -> Path:
    override = os.environ.get("NANO_ORCH_LLM_LOG", "").strip()
    if override:
        return Path(override)
    return _DEFAULT_LOG


def prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def append_llm_call(
    *,
    model_id: str,
    prompt: str,
    latency_ms: int,
    ok: bool,
    tokens_predicted: int | None = None,
    error: str | None = None,
    log_path: Path | None = None,
) -> Path:
    """Append one JSON line; never logs raw prompt (hash only)."""
    path = log_path or default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "prompt_hash": prompt_hash(prompt),
        "latency_ms": latency_ms,
        "ok": ok,
    }
    if tokens_predicted is not None:
        record["tokens_predicted"] = tokens_predicted
    if error:
        record["error"] = error
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    return path
