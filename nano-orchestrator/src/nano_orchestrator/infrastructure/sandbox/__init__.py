"""Composite sandbox — routes by TargetLanguage."""

from __future__ import annotations

from nano_orchestrator.domain.entities import MicroTask, TargetLanguage
from nano_orchestrator.domain.result import Err, Ok, Result
from nano_orchestrator.infrastructure.sandbox import ftl_sandbox, html_sandbox, js_sandbox


class CompositeSandbox:
    def run_checks(self, task: MicroTask, code: str) -> Result[dict[str, bool], str]:
        if task.language is TargetLanguage.JAVASCRIPT:
            return js_sandbox.check(code, task.acceptance)
        if task.language is TargetLanguage.HTML:
            return html_sandbox.check(code, task.acceptance)
        if task.language is TargetLanguage.FREEMARKER:
            return ftl_sandbox.check(code, task.acceptance)
        return Err("unsupported_language")
