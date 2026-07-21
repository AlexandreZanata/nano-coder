"""Unit tests for bake-off helpers (no GPU required)."""

from __future__ import annotations

from nano_orchestrator.application.bakeoff_metrics import BakeoffSummary, LangStats
from nano_orchestrator.application.codegen_prompts import extract_code
from nano_orchestrator.domain.entities import TargetLanguage


def test_extract_code_from_fence() -> None:
    raw = "Sure.\n```javascript\nexport const answer = 42;\n```\n"
    code = extract_code(raw, TargetLanguage.JAVASCRIPT)
    assert "export const answer = 42;" in code


def test_extract_html_stops_at_first_document() -> None:
    raw = (
        "<!DOCTYPE html><html><body><p>A</p></body></html>\n"
        "Language: html\n"
        "<!DOCTYPE html><html><body><p>B</p></body></html>\n"
    )
    code = extract_code(raw, TargetLanguage.HTML)
    assert "Language:" not in code
    assert code.count("</html>") == 1
    assert "A" in code and "B" not in code


def test_extract_code_trims_ftl_chatter() -> None:
    raw = (
        "<#list items as item><li>${item.name?html}</li></#list>\n"
        "Solution:\n<#list items as item><li>${item.name?html}</li></#list>\n"
    )
    code = extract_code(raw, TargetLanguage.FREEMARKER)
    assert code.count("<#list") == 1
    assert "Solution" not in code


def test_extract_rejects_js_filler_prefix() -> None:
    raw = (
        "Test case: cart = []\n"
        "export function total(cart) { return 0; }\n"
        "The code must be in a single fenced code block.\n"
    )
    code = extract_code(raw, TargetLanguage.JAVASCRIPT)
    assert code.strip().startswith("export function")
    assert "The code must" not in code


def test_looks_like_code_helpers() -> None:
    from nano_orchestrator.application.codegen_prompts import looks_like_code

    assert looks_like_code(
        "<!DOCTYPE html><html><body></body></html>\n", TargetLanguage.HTML
    )
    assert not looks_like_code("Latte and prices only prose\n", TargetLanguage.HTML)
    assert looks_like_code(
        "export function formatMoney(a) { return '$' + a.toFixed(2); }\n",
        TargetLanguage.JAVASCRIPT,
    )
    assert not looks_like_code(
        "export function formatMoney(a) {\n  // your code here\n}\n",
        TargetLanguage.JAVASCRIPT,
    )

def test_bakeoff_summary_p50_and_pass() -> None:
    summary = BakeoffSummary(
        model_id="demo",
        role="worker",
        by_lang={
            "javascript": LangStats(passed=2, total=4, latencies_ms=[100, 200]),
            "html": LangStats(passed=1, total=2, latencies_ms=[300]),
            "freemarker": LangStats(passed=0, total=0, latencies_ms=[]),
        },
    )
    assert summary.pass_at_1("javascript") == "0.50"
    assert summary.p50_ms() == "200"
    assert summary.overall_pass() == 0.5
