"""Contract tests for Stage 0 scope boundary artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_scope_boundary_yaml_exists_and_valid():
    path = ROOT / "config" / "scope-boundary.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["version"] == "v1"
    assert data["heldOutTestSetVersion"] == "held-out-v1"
    assert len(data["trainingTopics"]) >= 60
    assert len(data["heldOutTopics"]) == 150


def test_held_out_manifest_and_tasks_exist():
    manifest_path = ROOT / "data" / "benchmarks" / "held-out-v1" / "manifest.json"
    assert manifest_path.is_file(), "run scripts/bootstrap_held_out_tasks.py"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["taskCount"] == 150
    assert manifest["tasksPerLanguage"] == 50

    for lang_file in ("js.jsonl", "html.jsonl", "fmt.jsonl"):
        jsonl_path = ROOT / "data" / "benchmarks" / "held-out-v1" / lang_file
        text = jsonl_path.read_text(encoding="utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) == 50


def test_held_out_task_schema_file_exists():
    schema_path = ROOT / "config" / "held-out-v1" / "task.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["title"] == "HeldOutTask"
    assert "topicId" in schema["required"]
