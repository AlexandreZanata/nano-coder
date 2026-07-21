"""Parse orchestrator LLM output into MicroTask list (pure validation)."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from nano_orchestrator.domain.entities import MicroTask
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.domain.task_splitter import MAX_ACTIVE_WORKERS, validate_microtasks


def parse_microtasks_json(raw: str) -> Result[list[MicroTask], str]:
    text = raw.strip()
    for marker in ("<think>", "</think>"):
        if marker in text:
            text = text.split(marker, 1)[0].strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("[")
    if start < 0:
        return Err("invalid_json:no_array")
    try:
        data, _end = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as exc:
        return Err(f"invalid_json:{exc.msg}")
    if not isinstance(data, list):
        return Err("invalid_json:not_a_list")
    if len(data) > MAX_ACTIVE_WORKERS:
        return Err(f"worker_cap_exceeded:{len(data)}>{MAX_ACTIVE_WORKERS}")
    if not data:
        return Err("empty_task_list")
    tasks: list[MicroTask] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            return Err(f"invalid_item:{idx}:not_object")
        coerced = _coerce_microtask_item(item)
        try:
            tasks.append(MicroTask.model_validate(coerced))
        except ValidationError as exc:
            return Err(f"schema_error:{idx}:{exc.errors()[0]['msg']}")
    try:
        return Ok(validate_microtasks(tasks))
    except ValueError as exc:
        return Err(str(exc))


def _coerce_microtask_item(item: dict) -> dict:
    """Fill common missing fields from weak orchestrator output."""
    out = dict(item)
    if "role" not in out or out.get("role") in (None, ""):
        out["role"] = "coder"
    if "acceptance" not in out or out.get("acceptance") in (None, []):
        out["acceptance"] = ["syntax_valid"]
    if "prompt" not in out or not str(out.get("prompt") or "").strip():
        for alt in ("task", "description", "instruction"):
            if out.get(alt):
                out["prompt"] = str(out[alt])
                break
    if "id" not in out or not str(out.get("id") or "").strip():
        out["id"] = f"t-{abs(hash(str(out.get('prompt')))) % 10_000}"
    if "language" in out and isinstance(out["language"], str):
        lang = out["language"].strip().lower()
        aliases = {
            "js": "javascript",
            "htm": "html",
            "ftl": "freemarker",
            "stylesheet": "css",
        }
        out["language"] = aliases.get(lang, lang)
    if "constraints" in out and out["constraints"] is None:
        out["constraints"] = []
    if "max_tokens" in out and out["max_tokens"] is None:
        del out["max_tokens"]
    return out
