"""CSS sandbox — structural checks (no full CSS parser)."""

from __future__ import annotations

from nano_orchestrator.domain.result import Ok, Result


def check(code: str, acceptance: list[str]) -> Result[dict[str, bool], str]:
    checks: dict[str, bool] = {}
    if "syntax_valid" not in acceptance and acceptance:
        return Ok(checks)
    checks["syntax"] = _looks_like_css(code)
    return Ok(checks)


def _looks_like_css(code: str) -> bool:
    text = code.strip()
    if len(text) < 20:
        return False
    lower = text.lower()
    if "<html" in lower or "<!doctype" in lower:
        return False
    if "{" not in text or "}" not in text:
        return False
    # Require at least one common site rule target
    return any(
        token in lower
        for token in ("body", "nav", "header", ".hero", "a ", "button", ":root")
    )
