"""Prompt loading and placeholder rendering for teacher expansion."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.domain.target_language import TargetLanguage

_LANG_PREFIX = {
    TargetLanguage.JAVASCRIPT: "js",
    TargetLanguage.HTML: "html",
    TargetLanguage.FREEMARKER: "fmt",
}


class PromptRenderer:
    def __init__(self, prompt_dir: Path) -> None:
        self.prompt_dir = prompt_dir

    def load(self, name: str) -> str:
        path = self.prompt_dir / name
        return path.read_text(encoding="utf-8")

    def render(self, template: str, values: dict[str, str]) -> str:
        result = template
        for key, value in values.items():
            result = result.replace(f"{{{{{key}}}}}", value)
        return result

    @staticmethod
    def format_few_shot_seeds(seeds: list[dict]) -> str:
        blocks = []
        for seed in seeds:
            blocks.append(json.dumps(seed, indent=2, ensure_ascii=False))
        return "\n\n---\n\n".join(blocks)

    @staticmethod
    def lang_prefix(language: TargetLanguage) -> str:
        return _LANG_PREFIX[language]
