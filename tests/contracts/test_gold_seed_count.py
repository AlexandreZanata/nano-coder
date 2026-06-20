"""Contract tests for Stage 2 gold seed minimum (BR-001)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIN_SEEDS_PER_LANGUAGE = 50


def test_br001_minimum_gold_seeds_per_language():
    for folder in ("javascript", "html", "freemarker"):
        seed_dir = ROOT / "data" / "seeds" / folder
        seeds = [p for p in seed_dir.glob("seed-*.json") if p.is_file()]
        assert len(seeds) >= MIN_SEEDS_PER_LANGUAGE, (
            f"{folder}: {len(seeds)} seeds, need >= {MIN_SEEDS_PER_LANGUAGE}"
        )


def test_all_promoted_seeds_have_manual_metadata():
    for folder in ("javascript", "html", "freemarker"):
        for path in (ROOT / "data" / "seeds" / folder).glob("seed-*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            metadata = record.get("metadata", {})
            assert metadata.get("source") == "manual", path.name
            assert metadata.get("author") == "pipeline-operator", path.name
