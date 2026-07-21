"""HTML sandbox — prefer local html-validate; never hang smoke tests."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from nano_orchestrator.domain.result import Ok, Result


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    if "syntax_valid" not in acceptance and acceptance:
        return Ok(checks)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "snippet.html"
        path.write_text(code, encoding="utf-8")

        # Opt-in: NANO_ORCH_HTML_VALIDATE=1 (npx can be slow on first pull).
        use_npx = os.environ.get("NANO_ORCH_HTML_VALIDATE", "").strip() == "1"
        if use_npx and shutil.which("npx"):
            try:
                proc = subprocess.run(
                    ["npx", "--yes", "html-validate", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                checks["syntax"] = proc.returncode == 0
                return Ok(checks)
            except subprocess.TimeoutExpired:
                checks["syntax"] = False
                checks["html_validate_timeout"] = False
                return Ok(checks)

        # Fast default: well-formed enough for smoke (Phase 4 installs html-validate).
        checks["syntax"] = "<" in code and ">" in code
        checks["html_validate_skipped"] = True
        return Ok(checks)
