"""JavaScript sandbox — node --check (Phase 4 wiring)."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from nano_orchestrator.domain.result import Err, Ok, Result


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    if "syntax_valid" in acceptance or not acceptance:
        if not shutil.which("node"):
            return Err("node_not_found")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "snippet.js"
            path.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["node", "--check", str(path)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            checks["syntax"] = proc.returncode == 0
    return Ok(checks)
