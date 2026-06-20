#!/usr/bin/env python3
"""Export flat keyword blocklist for teacher prompts (.local/review/)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nano_coder.domain.scope_boundary import load_scope_boundary  # noqa: E402

OUTPUT = ROOT / ".local" / "review" / "held-out-leak-blocklist.txt"
SCOPE_PATH = ROOT / "config" / "scope-boundary.yaml"


def main() -> int:
    scope = load_scope_boundary(SCOPE_PATH)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Held-out leak blocklist — paste into teacher system prompt",
        "# Source: config/scope-boundary.yaml (BR-004)",
        "",
    ]
    for topic in scope.held_out_topics:
        keywords = ", ".join(topic.keywords)
        lines.append(f"{topic.id} [{topic.language.value}]: {topic.pattern} | {keywords}")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(scope.held_out_topics)} topics to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
