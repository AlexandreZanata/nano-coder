"""FreeMarker sandbox — JVM wrapper spike (Phase 4 / Day 8)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from nano_orchestrator.domain.result import Err, Ok, Result

SPIKE_JAR = (
    Path(__file__).resolve().parents[4]
    / "scripts"
    / "ftl_parser_spike"
    / "target"
    / "ftl-parser-spike.jar"
)


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    if "syntax_valid" not in acceptance and acceptance:
        return Ok(checks)
    if not SPIKE_JAR.is_file():
        # Honest stub: do not pretend FTL is validated.
        checks["syntax"] = False
        checks["ftl_spike_missing"] = False
        return Ok(checks)
    if not shutil.which("java"):
        return Err("java_not_found")
    proc = subprocess.run(
        ["java", "-jar", str(SPIKE_JAR)],
        input=code,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    checks["syntax"] = proc.returncode == 0
    return Ok(checks)
