"""Contract tests for promoted seed manifest (Stage 3, BR-001)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "data" / "seeds" / "manifest.json"


def test_promoted_seed_manifest_exists_and_satisfies_br001():
    assert MANIFEST.is_file(), "run scripts/promote_seeds.py --verify data/seeds/"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["passed"] is True
    assert manifest["br001Satisfied"] is True
    assert manifest["seedCount"] == 150
    for language in ("JavaScript", "HTML", "FreeMarker"):
        assert manifest["countsByLanguage"][language] >= 50


def test_manifest_lists_required_gates():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    gates = set(manifest["gatesRun"])
    assert "SchemaValidation" in gates
    assert "SyntaxValidation" in gates
    assert "HeldOutLeak" in gates
    assert "DuplicateCheck" in gates
