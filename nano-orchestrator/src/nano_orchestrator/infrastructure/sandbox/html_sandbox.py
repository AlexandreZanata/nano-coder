"""HTML sandbox — local html-validate when NANO_ORCH_HTML_VALIDATE=1."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from nano_orchestrator.domain.result import Ok, Result

_ROOT = Path(__file__).resolve().parents[4]
_LOCAL_BIN = _ROOT / "node_modules" / ".bin" / "html-validate"
_CONFIG = _ROOT / ".htmlvalidate.json"
_VALIDATE_TIMEOUT_S = 5
# Pinned fallback when local install missing (first pull may be slow).
_NPX_PIN = "html-validate@9.7.1"


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    if "syntax_valid" not in acceptance and acceptance:
        return Ok(checks)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "snippet.html"
        path.write_text(code, encoding="utf-8")

        use_validate = os.environ.get("NANO_ORCH_HTML_VALIDATE", "").strip() == "1"
        if use_validate:
            if not _has_html_structure(code):
                checks["syntax"] = False
                checks["html_structure"] = False
                return Ok(checks)
            return Ok(_run_html_validate(path, checks))

        checks["syntax"] = _has_html_structure(code)
        checks["html_validate_skipped"] = True
        return Ok(checks)


def _has_html_structure(code: str) -> bool:
    """Require at least one real HTML/FTL-ish tag; reject pure prose dumps."""
    import re

    if not re.search(r"<[a-zA-Z][a-zA-Z0-9:-]*\b", code):
        return False
    # Bullet lists pretending to be specs
    if code.count("<") == 0:
        return False
    return True


def _run_html_validate(path: Path, checks: dict[str, bool]) -> dict[str, bool]:
    cmd = _validate_command(path)
    if cmd is None:
        checks["syntax"] = False
        checks["html_validate_missing"] = False
        return checks
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_VALIDATE_TIMEOUT_S,
            check=False,
            cwd=str(_ROOT),
        )
        checks["syntax"] = proc.returncode == 0
        return checks
    except subprocess.TimeoutExpired:
        checks["syntax"] = False
        checks["html_validate_timeout"] = False
        return checks


def _validate_command(path: Path) -> list[str] | None:
    config_args = ["--config", str(_CONFIG)] if _CONFIG.is_file() else []
    if _LOCAL_BIN.is_file():
        return [str(_LOCAL_BIN), *config_args, str(path)]
    if shutil.which("npx"):
        return ["npx", "--yes", _NPX_PIN, *config_args, str(path)]
    return None
