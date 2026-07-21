#!/usr/bin/env python3
"""Validate gold_set.json and held_out.json against MicroTask schema + counts."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from nano_orchestrator.domain.entities import MicroTask

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "tests" / "golden" / "gold_set.json"
HELD = ROOT / "tests" / "golden" / "held_out.json"

GOLD_REQUIRED = {"javascript": 10, "html": 10, "freemarker": 10}
HELD_REQUIRED = {"javascript": 2, "html": 2, "freemarker": 2}


def _validate_file(
    path: Path,
    *,
    required: dict[str, int],
    id_prefix: str | None,
) -> list[str]:
    errors: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return [f"{path.name}: tasks must be a non-empty list"]

    counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    for raw in tasks:
        task_id = raw.get("id", "?")
        if task_id in seen_ids:
            errors.append(f"{path.name}: duplicate id {task_id}")
        seen_ids.add(str(task_id))
        if id_prefix and not str(task_id).startswith(id_prefix):
            errors.append(f"{path.name}: {task_id} must start with {id_prefix}")
        if "gold_code" not in raw or not str(raw["gold_code"]).strip():
            errors.append(f"{path.name}: {task_id} missing gold_code")
        payload = {k: v for k, v in raw.items() if k != "gold_code"}
        try:
            task = MicroTask.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path.name}: {task_id}: {exc}")
            continue
        counts[task.language.value] += 1

    for lang, need in required.items():
        got = counts.get(lang, 0)
        if got != need:
            errors.append(f"{path.name}: expected {need} {lang}, got {got}")

    total_need = sum(required.values())
    if len(tasks) != total_need:
        errors.append(f"{path.name}: expected {total_need} tasks, got {len(tasks)}")

    if not data.get("frozen"):
        errors.append(f"{path.name}: frozen must be true for v1 freeze (T-014)")

    return errors


def main() -> int:
    errors = _validate_file(GOLD, required=GOLD_REQUIRED, id_prefix=None)
    errors += _validate_file(HELD, required=HELD_REQUIRED, id_prefix="ho-")
    # Gold IDs should not collide with held-out
    gold_ids = {
        t["id"] for t in json.loads(GOLD.read_text(encoding="utf-8"))["tasks"]
    }
    held_ids = {
        t["id"] for t in json.loads(HELD.read_text(encoding="utf-8"))["tasks"]
    }
    overlap = gold_ids & held_ids
    if overlap:
        errors.append(f"id overlap between gold and held_out: {sorted(overlap)}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        print(f"FAIL: {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"OK: gold={sum(GOLD_REQUIRED.values())} held_out={sum(HELD_REQUIRED.values())}")
    print(f"OK: frozen v1 → {GOLD.name}, {HELD.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
