#!/usr/bin/env python3
"""Bootstrap HeldOutTestSet tasks from config/scope-boundary.yaml (Stage 0)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.scope_boundary import load_scope_boundary  # noqa: E402
from nano_coder.domain.target_language import TargetLanguage  # noqa: E402

OUTPUT_DIR = ROOT / "data" / "benchmarks" / "held-out-v1"
SCOPE_PATH = ROOT / "config" / "scope-boundary.yaml"

LANG_PREFIX = {
    TargetLanguage.JAVASCRIPT: ("js", "HO-JS"),
    TargetLanguage.HTML: ("html", "HO-HTML"),
    TargetLanguage.FREEMARKER: ("fmt", "HO-FMT"),
}


def build_instruction(topic_pattern: str, language: TargetLanguage) -> str:
    if language is TargetLanguage.JAVASCRIPT:
        return f"Implement {topic_pattern.lower()} in plain JavaScript (ES modules)."
    if language is TargetLanguage.HTML:
        return f"Build a complete HTML5 page for: {topic_pattern}."
    return f"Write a FreeMarker template for: {topic_pattern}."


def main() -> int:
    scope = load_scope_boundary(SCOPE_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_languages: dict[str, dict[str, int | str]] = {}
    total = 0

    for language in TargetLanguage:
        prefix, _ = LANG_PREFIX[language]
        topics = scope.held_out_topics_for(language)
        jsonl_path = OUTPUT_DIR / f"{prefix}.jsonl"
        lines: list[str] = []

        for index, topic in enumerate(topics, start=1):
            task_id = f"ho-{prefix}-{index:03d}"
            record = {
                "id": task_id,
                "targetLanguage": language.value,
                "topicId": topic.id,
                "instruction": build_instruction(topic.pattern, language),
                "tags": ["held-out", "L3-composite"],
                "acceptanceCriteria": {
                    "mustParse": True,
                    "mustContain": list(topic.keywords[:2]),
                    "mustNotContain": ["TODO", "FIXME", "your code here"],
                },
            }
            lines.append(json.dumps(record, ensure_ascii=False))

        jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        manifest_languages[prefix] = {"file": jsonl_path.name, "taskCount": len(lines)}
        total += len(lines)

    manifest = {
        "heldOutTestSetVersion": scope.held_out_test_set_version,
        "scopeBoundaryVersion": scope.version,
        "scopeBoundarySource": "config/scope-boundary.yaml",
        "taskCount": total,
        "tasksPerLanguage": 50,
        "languages": manifest_languages,
        "isolationRule": "BR-004",
        "immutable": True,
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {total} held-out tasks to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
