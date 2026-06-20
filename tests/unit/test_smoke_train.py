"""Unit tests for smoke train application (Stage 8)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_coder.application.smoke_train import run_smoke_train
from nano_coder.domain.smoke_train_config import load_smoke_train_config
from nano_coder.domain.training_run import TrainingRunState

ROOT = Path(__file__).resolve().parents[2]


def _write_published_dataset(published_root: Path, version: str, count: int) -> None:
    published_dir = published_root / version
    published_dir.mkdir(parents=True)
    lines = []
    for index in range(1, count + 1):
        record = {
            "id": f"syn-js-{index:04d}",
            "targetLanguage": "JavaScript",
            "instruction": f"Write a JavaScript helper #{index}.",
            "code": f"export function helper{index}() {{ return {index}; }}\n",
            "tags": ["functional", "module", "L2-standard"],
        }
        lines.append(json.dumps(record, ensure_ascii=False))
    (published_dir / "examples.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (published_dir / "manifest.json").write_text(
        json.dumps(
            {
                "datasetVersion": version,
                "state": "Published",
                "targetLanguage": "JavaScript",
                "exampleCount": count,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def test_run_smoke_train_dry_run(tmp_path):
    version = "ds-2026-06-20-js-v1"
    published_root = tmp_path / "datasets"
    _write_published_dataset(published_root, version, count=10)

    result = run_smoke_train(
        run_id="smoke-js-001",
        dataset_version=version,
        published_root=published_root,
        held_out_root=ROOT / "data" / "benchmarks" / "held-out-v1",
        checkpoint_root=tmp_path / "checkpoints",
        output_root=tmp_path / "output",
        config=load_smoke_train_config(ROOT / "config" / "smoke-train-v1.yaml"),
        dry_run=True,
    )

    assert result.train_example_count == 10
    assert result.eval_summary.task_count == 20
    assert result.manifest_path.is_file()
    assert result.training_state is TrainingRunState.COMPLETED
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["gateSatisfied"] is True
