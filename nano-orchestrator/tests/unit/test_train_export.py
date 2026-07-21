"""Unit tests for Phase 3 train export / held-out leak."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.application.train_export import (
    counts_meet_n,
    dedupe_examples,
    examples_from_gold,
    examples_from_teacher_jsonl,
    filter_held_out,
    group_by_language,
    write_jsonl,
)
from nano_orchestrator.domain.held_out_leak import leaks_held_out, load_held_out_blocklist
from nano_orchestrator.domain.train_example import TrainExample

ROOT = Path(__file__).resolve().parents[2]


def test_given_gold_when_export_then_examples_have_code() -> None:
    examples = examples_from_gold(ROOT / "tests" / "golden" / "gold_set.json")
    assert len(examples) >= 30
    assert all(ex.code.strip() for ex in examples)
    assert all(ex.source == "gold_seed" for ex in examples)


def test_given_held_out_prompt_when_filter_then_dropped() -> None:
    held = ROOT / "tests" / "golden" / "held_out.json"
    blocked = load_held_out_blocklist(held)
    task = json.loads(held.read_text(encoding="utf-8"))["tasks"][0]
    assert leaks_held_out(task["prompt"], task["gold_code"], blocked) is True
    examples = [
        TrainExample(
            id="leak",
            language=task["language"],
            instruction=task["prompt"],
            code=task["gold_code"],
            source="teacher_distill",
        ),
        TrainExample(
            id="ok",
            language="javascript",
            instruction="Export function add(a, b) that returns a+b",
            code="export function add(a, b) { return a + b; }\n",
            source="teacher_distill",
        ),
    ]
    kept, dropped = filter_held_out(examples, held)
    assert dropped == 1
    assert len(kept) == 1
    assert kept[0].id == "ok"


def test_given_teacher_rows_when_import_then_no_held_out_leak(tmp_path: Path) -> None:
    held = ROOT / "tests" / "golden" / "held_out.json"
    blocked = load_held_out_blocklist(held)
    parent = tmp_path / "teacher.jsonl"
    parent.write_text(
        json.dumps(
            {
                "id": "syn-1",
                "targetLanguage": "JavaScript",
                "instruction": "Write a uniqueSorted helper",
                "code": "export function uniqueSorted(xs) { return [...new Set(xs)].sort(); }",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    examples = examples_from_teacher_jsonl(
        parent, language="javascript", blocked=blocked, limit=10
    )
    assert len(examples) == 1
    assert examples[0].source == "teacher_distill"


def test_given_duplicates_when_dedupe_then_unique() -> None:
    a = TrainExample(
        id="1",
        language="html",
        instruction="form",
        code="<form></form>",
        source="gold_seed",
    )
    b = TrainExample(
        id="2",
        language="html",
        instruction="form",
        code="<form></form>",
        source="proposal",
    )
    assert len(dedupe_examples([a, b])) == 1


def test_given_n_when_counts_then_gate(tmp_path: Path) -> None:
    examples = [
        TrainExample(
            id=f"{lang}-{i}",
            language=lang,  # type: ignore[arg-type]
            instruction=f"task {i}",
            code=f"code {i}",
            source="teacher_distill",
        )
        for lang in ("javascript", "html", "freemarker")
        for i in range(50)
    ]
    grouped = group_by_language(examples)
    assert counts_meet_n(grouped, 50) is True
    path = tmp_path / "javascript" / "train.jsonl"
    assert write_jsonl(path, grouped["javascript"]) == 50
    assert path.is_file()


def test_sft_text_format() -> None:
    ex = TrainExample(
        id="x",
        language="javascript",
        instruction="Export clamp",
        code="export const clamp = (n, a, b) => Math.min(b, Math.max(a, n));",
        source="gold_seed",
    )
    text = ex.to_sft_text()
    assert "### Instruction:" in text
    assert "### Response:" in text
    assert "clamp" in text
