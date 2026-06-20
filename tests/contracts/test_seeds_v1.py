"""Contract tests for Stage 1 seed taxonomy and folder layout."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_seed_schema_and_taxonomy_exist():
    schema_path = ROOT / "config" / "seeds-v1" / "seed.schema.json"
    taxonomy_path = ROOT / "config" / "seeds-v1" / "taxonomy.yaml"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    taxonomy = yaml.safe_load(taxonomy_path.read_text(encoding="utf-8"))
    assert schema["title"] == "GoldSeedExample"
    assert len(taxonomy["difficultyTags"]) == 4
    assert set(taxonomy["domainTags"]) == {"JavaScript", "HTML", "FreeMarker"}


def test_data_seeds_folder_layout():
    for folder in ("javascript", "html", "freemarker", "reference"):
        assert (ROOT / "data" / "seeds" / folder).is_dir()
    refs = list((ROOT / "data" / "seeds" / "reference").glob("REF-*.json"))
    assert len(refs) == 3


def test_validate_seed_script_exists():
    assert (ROOT / "scripts" / "validate_seed.py").is_file()
