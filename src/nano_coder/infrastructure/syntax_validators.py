"""Syntax validators for seed promotion gates (BR-003). Infrastructure layer."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from html.parser import HTMLParser
from pathlib import Path

from nano_coder.domain.target_language import TargetLanguage


class SyntaxValidationError(Exception):
    """Code failed syntax validation for its TargetLanguage."""

    def __init__(self, language: TargetLanguage, message: str) -> None:
        self.language = language
        self.message = message
        super().__init__(f"SyntaxValidation [{language.value}]: {message}")


class LintValidationError(Exception):
    """JavaScript failed ESLint gate."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"LintPass: {message}")


_FMT_BLOCK_TAGS = frozenset({"if", "list", "macro", "attempt", "compress", "switch", "function", "recover"})
_FMT_SKIP_OPEN = frozenset({"else", "elseif", "break", "continue", "return", "sep", "assign", "global", "local"})
_FMT_DIRECTIVE = re.compile(r"</#(\w+)>|<#(\w+)\b")


_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


class _HTMLParseChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self._stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in _VOID_TAGS:
            self._stack.append(tag.lower())

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in _VOID_TAGS:
            return
        if not self._stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
            return
        expected = self._stack.pop()
        if expected != tag:
            self.errors.append(f"mismatched tag: expected </{expected}>, got </{tag}>")


def validate_javascript_syntax(code: str) -> None:
    """Parse-check JavaScript via Node when available (BR-003)."""
    node = shutil.which("node")
    if node is None:
        _validate_javascript_fallback(code)
        return

    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as handle:
        handle.write(code)
        temp_path = Path(handle.name)

    try:
        result = subprocess.run(
            [node, "--check", str(temp_path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "parse error").strip()
            raise SyntaxValidationError(TargetLanguage.JAVASCRIPT, detail)
    finally:
        temp_path.unlink(missing_ok=True)


def _validate_javascript_fallback(code: str) -> None:
    if "export " not in code and "function " not in code:
        raise SyntaxValidationError(TargetLanguage.JAVASCRIPT, "missing export or function declaration")
    if code.count("{") != code.count("}"):
        raise SyntaxValidationError(TargetLanguage.JAVASCRIPT, "unbalanced braces")


def validate_html_syntax(code: str) -> None:
    """Parse HTML5 markup with stdlib HTMLParser (BR-003)."""
    lowered = code.lower()
    if "<html" not in lowered:
        raise SyntaxValidationError(TargetLanguage.HTML, "missing <html> root element")

    parser = _HTMLParseChecker()
    try:
        parser.feed(code)
        parser.close()
    except Exception as exc:  # noqa: BLE001
        raise SyntaxValidationError(TargetLanguage.HTML, str(exc)) from exc

    if parser.errors:
        raise SyntaxValidationError(TargetLanguage.HTML, parser.errors[0])
    if parser._stack:  # noqa: SLF001
        unclosed = parser._stack[-1]
        raise SyntaxValidationError(TargetLanguage.HTML, f"unclosed tag <{unclosed}>")


def validate_freemarker_syntax(code: str) -> None:
    """Validate FreeMarker block structure and directive balance (BR-003)."""
    stack: list[str] = []
    for match in _FMT_DIRECTIVE.finditer(code):
        closing = match.group(1)
        if closing:
            tag = closing.lower()
            if not stack or stack[-1] != tag:
                raise SyntaxValidationError(
                    TargetLanguage.FREEMARKER,
                    f"unexpected </#{tag}> without matching opener",
                )
            stack.pop()
            continue

        opening = match.group(2).lower()
        if opening in _FMT_SKIP_OPEN:
            continue
        if opening in _FMT_BLOCK_TAGS:
            stack.append(opening)

    if stack:
        raise SyntaxValidationError(
            TargetLanguage.FREEMARKER,
            f"unclosed <#{stack[-1]}> block",
        )

    if "${" in code and "}" not in code:
        raise SyntaxValidationError(TargetLanguage.FREEMARKER, "unclosed ${ expression")


def validate_syntax(language: TargetLanguage, code: str) -> None:
    if language is TargetLanguage.JAVASCRIPT:
        validate_javascript_syntax(code)
    elif language is TargetLanguage.HTML:
        validate_html_syntax(code)
    else:
        validate_freemarker_syntax(code)


def validate_javascript_lint(code: str, eslint_config: Path) -> None:
    """Run ESLint on JavaScript seed code when npx is available."""
    npx = shutil.which("npx")
    if npx is None:
        return

    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as handle:
        handle.write(code)
        temp_path = Path(handle.name)

    try:
        result = subprocess.run(
            [
                npx,
                "--yes",
                "eslint@9",
                "--config",
                str(eslint_config),
                "--no-warn-ignored",
                str(temp_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stdout or result.stderr or "lint failed").strip()
            raise LintValidationError(detail)
    finally:
        temp_path.unlink(missing_ok=True)
