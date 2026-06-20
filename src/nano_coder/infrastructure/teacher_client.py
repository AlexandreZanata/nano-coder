"""TeacherModel API clients — Infrastructure layer (UC-001)."""

from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.request
from datetime import date

from nano_coder.domain.expansion_method import ExpansionMethod
from nano_coder.domain.target_language import TargetLanguage
from nano_coder.domain.teacher_response import TeacherResponse
from nano_coder.infrastructure.prompt_renderer import PromptRenderer


class AnthropicTeacherClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_tokens: int = 4096,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, *, system: str, user: str) -> TeacherResponse:
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"TeacherModel API error {exc.code}: {detail}") from exc

        text = body["content"][0]["text"]
        usage = body.get("usage", {})
        return TeacherResponse(
            text=text,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            model=self.model,
        )


class MockTeacherClient:
    """Deterministic teacher for tests and --dry-run (no API spend)."""

    def __init__(self, language: TargetLanguage) -> None:
        self.language = language
        self._counter = 0
        self._prefix = PromptRenderer.lang_prefix(language)

    def complete(self, *, system: str, user: str) -> TeacherResponse:
        self._counter += 1
        index = self._counter
        method = ExpansionMethod.SELF_INSTRUCT.value
        if "evol-deepen" in user:
            method = ExpansionMethod.EVOL_DEEPEN.value
        elif "evol-widen" in user:
            method = ExpansionMethod.EVOL_WIDEN.value
        elif "evol-shorten" in user:
            method = ExpansionMethod.EVOL_SHORTEN.value

        record = {
            "id": f"syn-{self._prefix}-{index:04d}",
            "targetLanguage": self.language.value,
            "instruction": (
                f"Write a {self.language.value} utility variant #{index} "
                f"following enterprise clean-code standards."
            ),
            "code": _mock_code(self.language, index),
            "tags": _mock_tags(self.language),
            "metadata": {
                "author": "teacher-model",
                "created": date.today().isoformat(),
                "source": "synthetic",
                "notes": f"expansion: {method}; dry-run mock",
            },
        }
        text = json.dumps(record, ensure_ascii=False)
        return TeacherResponse(
            text=text,
            input_tokens=800 + random.randint(0, 200),
            output_tokens=400 + random.randint(0, 100),
            model="mock-teacher",
        )


def _mock_tags(language: TargetLanguage) -> list[str]:
    if language is TargetLanguage.JAVASCRIPT:
        return ["functional", "module", "L2-standard"]
    if language is TargetLanguage.HTML:
        return ["semantic", "L2-standard"]
    return ["macro", "list", "L2-standard"]


def _mock_code(language: TargetLanguage, index: int) -> str:
    if language is TargetLanguage.JAVASCRIPT:
        return (
            f"/**\n * Mock synthetic utility #{index}\n"
            f" * @param {{number[]}} values\n * @returns {{number}}\n */\n"
            f"export function mockSum{index}(values) {{\n"
            f"  if (!Array.isArray(values)) throw new TypeError('values must be an array');\n"
            f"  return values.reduce((total, n) => total + n, 0);\n}}\n"
        )
    if language is TargetLanguage.HTML:
        return (
            f"<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
            f"  <meta charset=\"utf-8\" />\n  <title>Mock page {index}</title>\n"
            f"</head>\n<body>\n  <main><h1>Mock {index}</h1></main>\n</body>\n</html>\n"
        )
    return (
        f"<#-- Mock synthetic template #{index} -->\n"
        f"<#macro mockGreet{index} name>\n  <p>Hello ${{name?html}}</p>\n</#macro>\n"
    )


def build_teacher_client(
    *,
    language: TargetLanguage,
    dry_run: bool,
    model: str,
    max_tokens: int,
) -> AnthropicTeacherClient | MockTeacherClient:
    if dry_run:
        return MockTeacherClient(language)
    api_key = os.environ.get("TEACHER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("TEACHER_API_KEY is required unless --dry-run is set")
    return AnthropicTeacherClient(api_key=api_key, model=model, max_tokens=max_tokens)
