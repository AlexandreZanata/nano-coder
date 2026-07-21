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
    TargetLanguage.CSS: 0,
    TargetLanguage.HTML: 1,
    TargetLanguage.JAVASCRIPT: 2,
    TargetLanguage.FREEMARKER: 3,
}

_EXT = {
    TargetLanguage.JAVASCRIPT: "js",
    TargetLanguage.HTML: "html",
    TargetLanguage.FREEMARKER: "ftl",
    TargetLanguage.CSS: "css",
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
    filenames: dict[str, str] | None = None,
) -> Path:
    """Write code files + package.json under out/proposal only."""
    proposal = out_dir / "proposal"
    proposal.mkdir(parents=True, exist_ok=True)
    ordered = sort_tasks(tasks)
    files: list[dict] = []
    name_map = filenames or {}
    for task in ordered:
        response = responses[task.id]
        rel = name_map.get(task.id) or f"{task.id}.{_EXT[task.language]}"
        # Prevent path escape
        rel = Path(rel).name
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
        "openable": _openable_report(proposal, files),
    }
    package_path = proposal / "package.json"
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    return package_path


def _openable_report(proposal: Path, files: list[dict]) -> dict:
    """Which HTML pages can open as a mini-site (CSS linked + nav targets exist)."""
    names = {f["path"] for f in files}
    html_files = [f["path"] for f in files if f["path"].endswith(".html")]
    pages: dict[str, dict] = {}
    for name in html_files:
        text = (proposal / name).read_text(encoding="utf-8", errors="replace")
        has_css = 'href="styles.css"' in text or "href='styles.css'" in text
        missing_links: list[str] = []
        for href in _hrefs(text):
            if href.startswith(("http:", "https:", "mailto:", "#")):
                continue
            target = href.split("#", 1)[0]
            if target and target not in names and not (proposal / target).is_file():
                missing_links.append(href)
        pages[name] = {
            "linked_styles": has_css,
            "missing_links": missing_links,
            "opens": has_css and not missing_links and bool(text.strip()),
        }
    openable = [n for n, meta in pages.items() if meta["opens"]]
    archived_candidates = [n for n, meta in pages.items() if not meta["opens"]]
    return {
        "pages": pages,
        "openable": openable,
        "archive_candidates": archived_candidates,
        "has_styles": "styles.css" in names,
    }


def _hrefs(html: str) -> list[str]:
    import re

    return re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.I)


def archive_non_openable(
    *,
    out_dir: Path,
    label: str,
) -> dict:
    """Keep only openable HTML + styles.css in proposal/; archive the rest."""
    import shutil
    from datetime import date

    proposal = out_dir / "proposal"
    package_path = proposal / "package.json"
    if not package_path.is_file():
        return {"ok": False, "error": "missing_package"}
    package = json.loads(package_path.read_text(encoding="utf-8"))
    openable_meta = dict(package.get("openable") or {})
    openable = set(openable_meta.get("openable") or [])
    keep = set(openable)
    if (proposal / "styles.css").is_file():
        keep.add("styles.css")
    keep.add("package.json")

    stamp = f"{date.today().isoformat()}-{label}"
    dest = out_dir / "archive" / stamp
    moved: list[str] = []
    for path in sorted(proposal.iterdir()):
        if path.name in keep:
            continue
        if not path.is_file():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest / path.name))
        moved.append(path.name)

    if moved:
        note = {
            "reason": "non_openable_or_non_site_artifact",
            "kept_openable": sorted(openable),
            "moved": moved,
        }
        (dest / "ARCHIVE_NOTE.json").write_text(
            json.dumps(note, indent=2) + "\n", encoding="utf-8"
        )
    # Refresh openable report after moves
    files = [
        {
            "path": p.name,
            "task_id": "",
            "language": p.suffix.lstrip(".") or "unknown",
            "passed": True,
            "escalate_to_human": False,
            "score": None,
        }
        for p in sorted(proposal.iterdir())
        if p.is_file() and p.name != "package.json"
    ]
    package["openable"] = _openable_report(proposal, files)
    package["archived"] = {"label": stamp, "moved": moved}
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "archive": stamp, "kept": sorted(keep - {"package.json"}), "moved": moved}

