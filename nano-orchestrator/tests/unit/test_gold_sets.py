"""GIVEN frozen gold sets WHEN validated THEN counts and tools pass."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "tests" / "golden" / "gold_set.json"
HELD = ROOT / "tests" / "golden" / "held_out.json"
SCRIPTS = ROOT / "scripts"


def test_given_gold_set_when_loaded_then_thirty_tasks() -> None:
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    assert data["frozen"] is True
    assert data["counts"]["total"] == 30
    assert len(data["tasks"]) == 30


def test_given_held_out_when_loaded_then_six_tasks() -> None:
    data = json.loads(HELD.read_text(encoding="utf-8"))
    assert data["frozen"] is True
    assert data["counts"]["total"] == 6
    assert len(data["tasks"]) == 6
    assert all(t["id"].startswith("ho-") for t in data["tasks"])


def test_given_gold_and_held_out_when_ids_compared_then_no_overlap() -> None:
    gold_ids = {t["id"] for t in json.loads(GOLD.read_text(encoding="utf-8"))["tasks"]}
    held_ids = {t["id"] for t in json.loads(HELD.read_text(encoding="utf-8"))["tasks"]}
    assert gold_ids.isdisjoint(held_ids)


@pytest.mark.parametrize("script", ["validate_schema.py", "validate_gold_code.py"])
def test_given_validators_when_run_then_exit_zero(script: str) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
