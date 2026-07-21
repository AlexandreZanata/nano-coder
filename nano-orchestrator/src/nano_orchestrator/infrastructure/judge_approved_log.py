"""Append Judge-approved (prompt, code) pairs for Phase 3 export."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_LOG = _DEFAULT_ROOT / "logs" / "judge_approved.jsonl"


def default_judge_log_path() -> Path:
    override = os.environ.get("NANO_ORCH_JUDGE_LOG", "").strip()
    if override:
        return Path(override)
    return _DEFAULT_LOG


def append_judge_approved(
    *,
    task_id: str,
    language: str,
    instruction: str,
    code: str,
    score: float,
    model_id: str | None = None,
    log_path: Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> Path:
    path = log_path or default_judge_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "id": f"judge:{task_id}:{datetime.now(timezone.utc).strftime('%H%M%S')}",
        "task_id": task_id,
        "language": language,
        "instruction": instruction,
        "code": code,
        "passed": True,
        "score": score,
        "model_id": model_id,
        "metadata": metadata or {},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path
