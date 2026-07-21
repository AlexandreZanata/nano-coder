"""JavaScript sandbox — node --check + optional vm exec (ASI07 timeout)."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from nano_orchestrator.domain.result import Err, Ok, Result

_EXEC_TIMEOUT_MS = 1000
_NODE_TIMEOUT_S = 10


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    want_syntax = (not acceptance) or ("syntax_valid" in acceptance)
    want_exec = "exec_ok" in acceptance

    if not want_syntax and not want_exec:
        return Ok(checks)
    if not shutil.which("node"):
        return Err("node_not_found")

    if want_syntax:
        checks["syntax"] = _node_check(code) and _has_js_body(code)
    if want_exec:
        checks["exec"] = _vm_exec(code)
    return Ok(checks)


def _has_js_body(code: str) -> bool:
    """Reject empty stubs that still pass node --check."""
    lower = code.lower()
    if "your code here" in lower or re.search(r"\btodo\b", lower):
        return False
    if "export " not in code:
        return False
    # Empty function bodies: export function f() {}
    if re.search(r"function\s+[A-Za-z0-9_]+\s*\([^)]*\)\s*\{\s*\}", code):
        return False
    return True


def _node_check(code: str) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "snippet.js"
        path.write_text(code, encoding="utf-8")
        proc = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True,
            text=True,
            timeout=_NODE_TIMEOUT_S,
            check=False,
        )
        return proc.returncode == 0


def _vm_exec(code: str) -> bool:
    """Run snippet in node vm with timeout; empty sandbox (no require/fs)."""
    runner = (
        "const vm = require('vm');\n"
        "const code = process.argv[1];\n"
        f"const timeout = {_EXEC_TIMEOUT_MS};\n"
        "try {\n"
        "  vm.runInNewContext(code, Object.create(null), { timeout, displayErrors: true });\n"
        "  process.exit(0);\n"
        "} catch (err) {\n"
        "  process.stderr.write(String(err && err.message ? err.message : err));\n"
        "  process.exit(1);\n"
        "}\n"
    )
    try:
        proc = subprocess.run(
            ["node", "-e", runner, code],
            capture_output=True,
            text=True,
            timeout=_NODE_TIMEOUT_S,
            check=False,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False
