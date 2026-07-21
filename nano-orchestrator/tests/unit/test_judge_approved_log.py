"""Tests for judge-approved log append."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.infrastructure.judge_approved_log import append_judge_approved


def test_append_judge_approved_writes_pair(tmp_path: Path) -> None:
    path = tmp_path / "judge_approved.jsonl"
    append_judge_approved(
        task_id="t1",
        language="javascript",
        instruction="Export clamp",
        code="export const clamp = (n,a,b)=>Math.min(b,Math.max(a,n));\n",
        score=0.9,
        model_id="qwen25-coder-0.5b",
        log_path=path,
    )
    row = json.loads(path.read_text(encoding="utf-8").strip())
    assert row["passed"] is True
    assert row["language"] == "javascript"
    assert "clamp" in row["code"]
    assert row["instruction"]
