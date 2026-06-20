"""Contract tests for Stage 4 generation prompts and config."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PROMPTS = (
    "self-instruct-system.md",
    "self-instruct-user.md",
    "evol-instruct-deepen.md",
    "evol-instruct-widen.md",
    "evol-instruct-shorten.md",
)


def test_generation_config_and_prompts_exist():
    config = yaml.safe_load((ROOT / "config" / "generation-v1.yaml").read_text(encoding="utf-8"))
    assert config["defaults"]["targetCount"] >= 1500
    prompt_dir = ROOT / "config" / "prompts" / "v1"
    for name in REQUIRED_PROMPTS:
        path = prompt_dir / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert "{{TARGET_LANGUAGE}}" in text or "{{OUT_OF_SCOPE}}" in text or "Base example" in text


def test_generate_synthetic_script_exists():
    assert (ROOT / "scripts" / "generate_synthetic.py").is_file()
