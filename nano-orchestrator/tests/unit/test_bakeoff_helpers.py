"""Unit tests for bake-off helpers (no GPU required)."""

from __future__ import annotations

from nano_orchestrator.application.bakeoff_metrics import BakeoffSummary, LangStats
from nano_orchestrator.application.codegen_prompts import extract_code
from nano_orchestrator.domain.entities import TargetLanguage


def test_extract_code_from_fence() -> None:
    raw = "Sure.\n```javascript\nexport const answer = 42;\n```\n"
    code = extract_code(raw, TargetLanguage.JAVASCRIPT)
    assert "export const answer = 42;" in code


def test_extract_code_html_strips_preamble() -> None:
    raw = "Here is the markup:\n<form method=\"post\"></form>\n"
    code = extract_code(raw, TargetLanguage.HTML)
    assert code.lstrip().startswith("<form")


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
