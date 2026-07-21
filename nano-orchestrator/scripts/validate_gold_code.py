#!/usr/bin/env python3
"""Validate gold_code snippets with real tools (node --check + HTML heuristics)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "tests" / "golden" / "gold_set.json",
    ROOT / "tests" / "golden" / "held_out.json",
]


def _check_js(code: str, task_id: str) -> str | None:
    if not shutil.which("node"):
        return f"{task_id}: node not found"
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{task_id}.mjs"
        path.write_text(code, encoding="utf-8")
        proc = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if proc.returncode != 0:
            return f"{task_id}: node --check failed: {proc.stderr.strip()}"
    return None


def _check_html(code: str, task_id: str) -> str | None:
    if "<" not in code or ">" not in code:
        return f"{task_id}: HTML missing tags"
    forbidden = ("onclick=", "<script", "javascript:")
    lower = code.lower()
    for token in forbidden:
        if token in lower:
            return f"{task_id}: forbidden HTML token {token}"
    return None


def _check_ftl(code: str, task_id: str) -> str | None:
    # Structural sanity until JVM spike (T-042) is wired.
    if "<#" not in code and "${" not in code:
        return f"{task_id}: FreeMarker missing directives or interpolations"
    if "?eval" in code:
        return f"{task_id}: ?eval forbidden"
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
            if lang == "javascript":
                err = _check_js(code, task_id)
            elif lang == "html":
                err = _check_html(code, task_id)
            elif lang == "freemarker":
                err = _check_ftl(code, task_id)
            else:
                err = f"{task_id}: unknown language {lang}"
            if err:
                errors.append(err)
            checked += 1

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        print(f"FAIL: {len(errors)}/{checked} snippet(s)", file=sys.stderr)
        return 1

    print(f"OK: {checked} gold_code snippet(s) passed tool checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
