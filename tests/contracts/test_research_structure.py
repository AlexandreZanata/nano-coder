"""Contract tests for research lab structure."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_experiments_yaml_loads():
    path = ROOT / "config" / "experiments.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert "experiments" in data
    assert "profiles" in data
    assert "ci" in data["profiles"]
    assert "publication" in data["profiles"]


def test_every_registered_experiment_has_folder():
    config = yaml.safe_load((ROOT / "config" / "experiments.yaml").read_text(encoding="utf-8"))
    for key in config["experiments"]:
        exp_dir = ROOT / "experiments" / key
        assert exp_dir.is_dir(), f"missing folder for registered experiment: {key}"
        assert (exp_dir / "hypothesis.md").is_file()
        assert (exp_dir / "run.py").is_file()


def test_paper_narrative_experiments_exist():
    narrative = (ROOT / "docs" / "PAPER-NARRATIVE.md").read_text(encoding="utf-8")
    config = yaml.safe_load((ROOT / "config" / "experiments.yaml").read_text(encoding="utf-8"))
    keys = set(config["experiments"])
    for line in narrative.splitlines():
        if "| exp_" in line and "|" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            for part in parts:
                if part.startswith("exp_"):
                    if part in keys:
                        continue
                    matches = [k for k in keys if k.startswith(part + "_") or k == part]
                    assert matches, f"paper narrative references unknown {part}"


def test_citation_cff_has_mit_license():
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "license: MIT" in text
