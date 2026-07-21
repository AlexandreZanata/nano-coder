#!/usr/bin/env python3
"""Validate gold_code snippets via Phase 4 sandboxes."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_orchestrator.infrastructure.sandbox import ftl_sandbox, html_sandbox, js_sandbox  # noqa: E402

FILES = [
    ROOT / "tests" / "golden" / "gold_set.json",
    ROOT / "tests" / "golden" / "held_out.json",
]


def _fail(task_id: str, detail: str) -> str:
    return f"{task_id}: {detail}"


def _check_js(code: str, acceptance: list[str], task_id: str) -> str | None:
    result = js_sandbox.check(code, acceptance)
    if result.is_err():
        return _fail(task_id, str(result.error))
    checks = result.value  # type: ignore[union-attr]
    if checks.get("syntax") is False:
        return _fail(task_id, "js syntax failed")
    return None


def _check_html(code: str, acceptance: list[str], task_id: str) -> str | None:
    # Prefer real html-validate when installed; else heuristic path.
    if (ROOT / "node_modules" / ".bin" / "html-validate").is_file():
        os.environ["NANO_ORCH_HTML_VALIDATE"] = "1"
    result = html_sandbox.check(code, acceptance)
    if result.is_err():
        return _fail(task_id, str(result.error))
    checks = result.value  # type: ignore[union-attr]
    if checks.get("syntax") is not True:
        return _fail(task_id, f"html syntax failed ({checks})")
    return None


def _check_ftl(code: str, acceptance: list[str], task_id: str) -> str | None:
    if not ftl_sandbox.jar_ready():
        return _fail(task_id, f"FTL spike missing — {ftl_sandbox.build_hint()}")
    result = ftl_sandbox.check(code, acceptance)
    if result.is_err():
        return _fail(task_id, str(result.error))
    checks = result.value  # type: ignore[union-attr]
    if checks.get("syntax") is not True:
        return _fail(task_id, f"ftl syntax failed ({checks})")
    return None


def main() -> int:
    errors: list[str] = []
    checked = 0
    for path in FILES:
        tasks = json.loads(path.read_text(encoding="utf-8"))["tasks"]
        for task in tasks:
            task_id = task["id"]
            code = task["gold_code"]
            lang = task["language"]
            acceptance = list(task.get("acceptance") or ["syntax_valid"])
            if lang == "javascript":
                err = _check_js(code, acceptance, task_id)
            elif lang == "html":
                err = _check_html(code, acceptance, task_id)
            elif lang == "freemarker":
                err = _check_ftl(code, acceptance, task_id)
            else:
                err = _fail(task_id, f"unknown language {lang}")
            if err:
                errors.append(err)
            checked += 1

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        print(f"FAIL: {len(errors)}/{checked} snippet(s)", file=sys.stderr)
        return 1

    print(f"OK: {checked} gold_code snippet(s) passed sandbox checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
