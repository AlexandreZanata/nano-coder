"""Held-out leakage checks for Phase 3 train export (BR-004)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_WS = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    return _WS.sub(" ", text.strip().lower())


def load_held_out_blocklist(held_out_path: Path) -> set[str]:
    """Return normalized prompt + gold_code strings that MUST NOT appear in train."""
    payload = json.loads(held_out_path.read_text(encoding="utf-8"))
    blocked: set[str] = set()
    for task in payload.get("tasks", []):
        prompt = task.get("prompt") or task.get("instruction") or ""
        code = task.get("gold_code") or ""
        if prompt.strip():
            blocked.add(normalize_text(prompt))
        if code.strip():
            blocked.add(normalize_text(code))
    return blocked


def leaks_held_out(instruction: str, code: str, blocked: set[str]) -> bool:
    if not blocked:
        return False
    instr = normalize_text(instruction)
    body = normalize_text(code)
    if instr in blocked or body in blocked:
        return True
    for item in blocked:
        if len(item) < 24:
            continue
        if item in instr or item in body:
            return True
    return False
