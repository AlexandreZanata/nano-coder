"""Export / merge Judge-approved and teacher-distill train JSONL."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from nano_orchestrator.domain.held_out_leak import leaks_held_out, load_held_out_blocklist
from nano_orchestrator.domain.train_example import TrainExample

DEFAULT_N_MIN = 50
LANGS = ("javascript", "html", "freemarker")


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, examples: Iterable[TrainExample]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example.to_jsonl_dict(), ensure_ascii=False) + "\n")
            count += 1
    return count


def examples_from_gold(gold_path: Path) -> list[TrainExample]:
    payload = json.loads(gold_path.read_text(encoding="utf-8"))
    out: list[TrainExample] = []
    for task in payload.get("tasks", []):
        out.append(
            TrainExample(
                id=f"gold:{task['id']}",
                language=task["language"],
                instruction=task["prompt"],
                code=task["gold_code"],
                source="gold_seed",
                task_id=task["id"],
                metadata={"note": "human gold seed — not held_out"},
            )
        )
    return out


def examples_from_proposal(proposal_dir: Path) -> list[TrainExample]:
    package_path = proposal_dir / "package.json"
    if not package_path.is_file():
        return []
    package = json.loads(package_path.read_text(encoding="utf-8"))
    out: list[TrainExample] = []
    for entry in package.get("files", []):
        if not entry.get("passed"):
            continue
        rel = entry.get("path")
        if not rel:
            continue
        code_path = proposal_dir / rel
        if not code_path.is_file():
            continue
        code = code_path.read_text(encoding="utf-8")
        task_id = str(entry.get("task_id") or code_path.stem)
        language = entry.get("language")
        if language not in LANGS:
            continue
        instruction = _instruction_from_proposal(package, task_id, language)
        out.append(
            TrainExample(
                id=f"proposal:{task_id}",
                language=language,
                instruction=instruction,
                code=code,
                source="proposal",
                task_id=task_id,
                score=float(entry.get("score") or 0.0) or None,
                metadata={"human_gate": True},
            )
        )
    return out


def examples_from_judge_log(log_path: Path) -> list[TrainExample]:
    out: list[TrainExample] = []
    for row in load_jsonl(log_path):
        if not row.get("passed"):
            continue
        language = row.get("language")
        instruction = row.get("instruction") or row.get("prompt")
        code = row.get("code")
        if language not in LANGS or not instruction or not code:
            continue
        out.append(
            TrainExample(
                id=str(row.get("id") or f"judge:{row.get('task_id')}"),
                language=language,
                instruction=str(instruction),
                code=str(code),
                source="judge_log",
                task_id=row.get("task_id"),
                model_id=row.get("model_id"),
                score=row.get("score"),
                metadata=dict(row.get("metadata") or {}),
            )
        )
    return out


def examples_from_teacher_jsonl(
    path: Path,
    *,
    language: str,
    blocked: set[str],
    limit: int | None = None,
) -> list[TrainExample]:
    out: list[TrainExample] = []
    for row in load_jsonl(path):
        instruction = str(row.get("instruction") or "").strip()
        code = str(row.get("code") or "").strip()
        if not instruction or not code:
            continue
        if leaks_held_out(instruction, code, blocked):
            continue
        eid = str(row.get("id") or f"teacher-{len(out)}")
        out.append(
            TrainExample(
                id=f"teacher:{eid}",
                language=language,  # type: ignore[arg-type]
                instruction=instruction,
                code=code,
                source="teacher_distill",
                metadata={
                    "parent_id": eid,
                    "parent_language": row.get("targetLanguage"),
                    "tags": row.get("tags") or [],
                },
            )
        )
        if limit is not None and len(out) >= limit:
            break
    return out


def dedupe_examples(examples: list[TrainExample]) -> list[TrainExample]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[TrainExample] = []
    for example in examples:
        key = (
            example.language,
            example.instruction.strip(),
            example.code.strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(example)
    return unique


def filter_held_out(
    examples: list[TrainExample], held_out_path: Path
) -> tuple[list[TrainExample], int]:
    blocked = load_held_out_blocklist(held_out_path)
    kept: list[TrainExample] = []
    dropped = 0
    for example in examples:
        if leaks_held_out(example.instruction, example.code, blocked):
            dropped += 1
            continue
        kept.append(example)
    return kept, dropped


def group_by_language(
    examples: list[TrainExample],
) -> dict[str, list[TrainExample]]:
    grouped: dict[str, list[TrainExample]] = defaultdict(list)
    for example in examples:
        grouped[example.language].append(example)
    return dict(grouped)


def counts_meet_n(grouped: dict[str, list[TrainExample]], n_min: int) -> bool:
    return all(len(grouped.get(lang, [])) >= n_min for lang in LANGS)


def _instruction_from_proposal(package: dict, task_id: str, language: str) -> str:
    request = str(package.get("request") or "").strip()
    if request:
        return f"{request} (task {task_id}, language {language})"
    return f"Generate {language} code for task {task_id}"
