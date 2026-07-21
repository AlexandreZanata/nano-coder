"""FreeMarker sandbox — JVM wrapper on ftl-parser-spike.jar."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from nano_orchestrator.domain.result import Err, Ok, Result

_SPIKE_ROOT = Path(__file__).resolve().parents[4] / "scripts" / "ftl_parser_spike"
SPIKE_JAR = _SPIKE_ROOT / "target" / "ftl-parser-spike.jar"
_BUILD_SH = _SPIKE_ROOT / "build.sh"


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    if "syntax_valid" not in acceptance and acceptance:
        return Ok(checks)
    if not SPIKE_JAR.is_file():
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
        cwd=str(SPIKE_JAR.parent),
    )
    checks["syntax"] = proc.returncode == 0
    return Ok(checks)


def jar_ready() -> bool:
    return SPIKE_JAR.is_file()


def build_hint() -> str:
    return f"Run: {_BUILD_SH}"
