"""Deterministic merge of worker outputs into out/proposal/ (human gate)."""

from __future__ import annotations

import json
from pathlib import Path

from nano_orchestrator.domain.entities import (
    JudgeVerdict,
    MicroTask,
    TargetLanguage,
    WorkerResponse,
)

_LANG_ORDER = {
    TargetLanguage.JAVASCRIPT: 0,
    TargetLanguage.HTML: 1,
    TargetLanguage.FREEMARKER: 2,
}

_EXT = {
    TargetLanguage.JAVASCRIPT: "js",
    TargetLanguage.HTML: "html",
    TargetLanguage.FREEMARKER: "ftl",
}


def sort_tasks(tasks: list[MicroTask]) -> list[MicroTask]:
    return sorted(tasks, key=lambda t: (_LANG_ORDER[t.language], t.id))


def write_proposal(
    *,
    out_dir: Path,
    request: str,
    tasks: list[MicroTask],
    responses: dict[str, WorkerResponse],
    verdicts: dict[str, JudgeVerdict],
    escalate: dict[str, bool],
    peak_vram_mb: int | None,
) -> Path:
    """Write code files + package.json under out/proposal only."""
    proposal = out_dir / "proposal"
    proposal.mkdir(parents=True, exist_ok=True)
    ordered = sort_tasks(tasks)
    files: list[dict] = []
    for task in ordered:
        response = responses[task.id]
        ext = _EXT[task.language]
        rel = f"{task.id}.{ext}"
        (proposal / rel).write_text(response.code, encoding="utf-8")
        files.append(
            {
                "path": rel,
                "task_id": task.id,
                "language": task.language.value,
                "passed": verdicts[task.id].passed,
                "escalate_to_human": escalate.get(task.id, False),
                "score": verdicts[task.id].score,
            }
        )
    package = {
        "request": request,
        "human_gate": True,
        "auto_persist": False,
        "peak_vram_mb": peak_vram_mb,
        "files": files,
        "verdicts": {
            tid: v.model_dump(mode="json") for tid, v in verdicts.items()
        },
    }
    package_path = proposal / "package.json"
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    return package_path
