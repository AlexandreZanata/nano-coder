"""CLI parser and offline decompose/judge (T-071)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.cli import build_parser, main

ROOT = Path(__file__).resolve().parents[2]


def test_parser_has_decompose_judge_bakeoff() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for name in ("decompose", "judge", "bakeoff", "smoke", "version", "large-site"):
        assert name in help_text


def test_version_exit_zero() -> None:
    assert main(["version"]) == 0


def test_decompose_json_file(tmp_path: Path) -> None:
    payload = [
        {
            "id": "t1",
            "role": "coder",
            "language": "javascript",
            "prompt": "export x",
            "acceptance": ["syntax_valid"],
            "max_tokens": 64,
        }
    ]
    path = tmp_path / "tasks.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert main(["decompose", "--json-file", str(path)]) == 0


def test_decompose_cap_exceeded(tmp_path: Path) -> None:
    payload = [
        {
            "id": f"t{i}",
            "role": "coder",
            "language": "javascript",
            "prompt": "p",
            "acceptance": ["syntax_valid"],
        }
        for i in range(6)
    ]
    path = tmp_path / "too_many.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert main(["decompose", "--json-file", str(path)]) == 1


def test_judge_gold_js(tmp_path: Path) -> None:
    gold = json.loads((ROOT / "tests" / "golden" / "gold_set.json").read_text())
    task = next(t for t in gold["tasks"] if t["id"] == "js-001")
    code_path = tmp_path / "js001.js"
    code_path.write_text(task["gold_code"], encoding="utf-8")
    rc = main(
        [
            "judge",
            "--task-id",
            "js-001",
            "--language",
            "javascript",
            "--code-file",
            str(code_path),
            "--acceptance",
            "syntax_valid",
        ]
    )
    assert rc == 0
