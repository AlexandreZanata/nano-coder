"""GIVEN/WHEN/THEN — Judge sandboxes (Phase 4)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from nano_orchestrator.infrastructure.sandbox import ftl_sandbox, html_sandbox, js_sandbox

ROOT = Path(__file__).resolve().parents[2]


def test_given_valid_js_when_syntax_check_then_true() -> None:
    result = js_sandbox.check("export const x = 1;\n", ["syntax_valid"])
    assert result.is_ok()
    assert result.value["syntax"] is True  # type: ignore[union-attr]


def test_given_empty_js_stub_when_syntax_check_then_false() -> None:
    stub = "export function formatMoney(amount) {\n  // your code here\n}\n"
    result = js_sandbox.check(stub, ["syntax_valid"])
    assert result.is_ok()
    assert result.value["syntax"] is False  # type: ignore[union-attr]


def test_given_invalid_js_when_syntax_check_then_false() -> None:
    result = js_sandbox.check("function (\n", ["syntax_valid"])
    assert result.is_ok()
    assert result.value["syntax"] is False  # type: ignore[union-attr]


def test_given_exec_ok_when_vm_runs_then_exec_true() -> None:
    result = js_sandbox.check("const n = 1 + 1;\n", ["exec_ok"])
    assert result.is_ok()
    assert result.value["exec"] is True  # type: ignore[union-attr]
    assert "syntax" not in result.value  # type: ignore[index]


def test_given_exec_ok_when_vm_throws_then_exec_false() -> None:
    result = js_sandbox.check("throw new Error('boom');\n", ["exec_ok"])
    assert result.is_ok()
    assert result.value["exec"] is False  # type: ignore[union-attr]


def test_given_html_validate_off_when_tags_present_then_skipped() -> None:
    os.environ.pop("NANO_ORCH_HTML_VALIDATE", None)
    result = html_sandbox.check("<p>Hi</p>\n", ["syntax_valid"])
    assert result.is_ok()
    checks = result.value  # type: ignore[union-attr]
    assert checks["syntax"] is True
    assert checks.get("html_validate_skipped") is True


@pytest.mark.skipif(
    not (ROOT / "node_modules" / ".bin" / "html-validate").is_file(),
    reason="html-validate not installed (npm install)",
)
def test_given_html_validate_on_when_good_snippet_then_syntax_true() -> None:
    os.environ["NANO_ORCH_HTML_VALIDATE"] = "1"
    try:
        result = html_sandbox.check(
            '<form method="post" action="/x"><button type="submit">Go</button></form>\n',
            ["syntax_valid"],
        )
        assert result.is_ok()
        assert result.value["syntax"] is True  # type: ignore[union-attr]
        assert "html_validate_skipped" not in result.value  # type: ignore[operator]
    finally:
        os.environ.pop("NANO_ORCH_HTML_VALIDATE", None)


@pytest.mark.skipif(
    not (ROOT / "node_modules" / ".bin" / "html-validate").is_file(),
    reason="html-validate not installed (npm install)",
)
def test_given_html_validate_on_when_unclosed_then_syntax_false() -> None:
    os.environ["NANO_ORCH_HTML_VALIDATE"] = "1"
    try:
        result = html_sandbox.check("<form><button>x\n", ["syntax_valid"])
        assert result.is_ok()
        assert result.value["syntax"] is False  # type: ignore[union-attr]
    finally:
        os.environ.pop("NANO_ORCH_HTML_VALIDATE", None)


@pytest.mark.skipif(
    not ftl_sandbox.jar_ready(),
    reason="FTL spike jar missing — run scripts/ftl_parser_spike/build.sh",
)
def test_given_valid_ftl_when_check_then_syntax_true() -> None:
    result = ftl_sandbox.check("<#list items as i>${i}</#list>\n", ["syntax_valid"])
    assert result.is_ok()
    assert result.value["syntax"] is True  # type: ignore[union-attr]
    assert "ftl_spike_missing" not in result.value  # type: ignore[operator]


@pytest.mark.skipif(
    not ftl_sandbox.jar_ready(),
    reason="FTL spike jar missing — run scripts/ftl_parser_spike/build.sh",
)
def test_given_invalid_ftl_when_check_then_syntax_false() -> None:
    result = ftl_sandbox.check("<#list items as i>${i}\n", ["syntax_valid"])
    assert result.is_ok()
    assert result.value["syntax"] is False  # type: ignore[union-attr]


@pytest.mark.skipif(
    not ftl_sandbox.jar_ready(),
    reason="FTL spike jar missing — run scripts/ftl_parser_spike/build.sh",
)
def test_given_gold_ftl_when_check_then_all_syntax_true() -> None:
    import json

    tasks = json.loads((ROOT / "tests" / "golden" / "gold_set.json").read_text(encoding="utf-8"))[
        "tasks"
    ]
    for task in tasks:
        if task["language"] != "freemarker":
            continue
        result = ftl_sandbox.check(task["gold_code"], task["acceptance"])
        assert result.is_ok(), task["id"]
        assert result.value["syntax"] is True, task["id"]  # type: ignore[union-attr]
