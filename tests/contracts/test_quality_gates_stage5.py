"""Contract tests for Stage 5 quality gates configuration."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_quality_gates_config_exists():
    path = ROOT / "config" / "quality-gates-v1.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["version"] == "v1"
    assert raw["gates"]["schemaValidation"] is True
    assert raw["publishDefaults"]["minAcceptedPerLanguage"] == 1500


def test_synthetic_schema_exists():
    path = ROOT / "config" / "seeds-v1" / "synthetic.schema.json"
    schema = json.loads(path.read_text(encoding="utf-8"))
    assert schema["title"] == "SyntheticExample"
    assert "syn-(js|html|fmt)" in schema["properties"]["id"]["pattern"]


def test_filter_synthetic_script_exists():
    assert (ROOT / "scripts" / "filter_synthetic.py").is_file()


def test_taxonomy_includes_synthetic_id_pattern():
    taxonomy_path = ROOT / "config" / "seeds-v1" / "taxonomy.yaml"
    taxonomy = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    assert "synthetic" in taxonomy["idPatterns"]
    assert "syn-" in taxonomy["idPatterns"]["synthetic"]
