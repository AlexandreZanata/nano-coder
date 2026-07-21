"""Map open-source Tier-A front-end datasets to nano-coder SyntheticExample records."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterator

_IMPERATIVE_PREFIXES = (
    "Write ",
    "Create ",
    "Build ",
    "Implement ",
    "Develop ",
    "Design ",
    "Construct ",
    "Produce ",
    "Generate ",
    "Add ",
    "Render ",
    "Define ",
)

_REACT_FRAMEWORK = re.compile(
    r"\b(react|vue|angular|svelte|next\.js|nextjs|tailwind|bootstrap)\b",
    re.IGNORECASE,
)
_HTML_ROOT = re.compile(r"<html\b", re.IGNORECASE)


def has_html_document_root(code: str) -> bool:
    """Tier-A import requires a full HTML document, not CSS-only snippets."""
    return _HTML_ROOT.search(code) is not None


def ensure_imperative_instruction(text: str) -> str:
    stripped = text.strip()
    lowered = stripped.lower()
    for prefix in _IMPERATIVE_PREFIXES:
        if lowered.startswith(prefix.lower()):
            return stripped
    return f"Write {stripped}"


def is_in_scope_front_end_code(code: str) -> bool:
    return _REACT_FRAMEWORK.search(code) is None


def infer_html_tags(instruction: str, code: str) -> list[str]:
    blob = f"{instruction}\n{code}".lower()
    tags: list[str] = ["L2-standard"]
    if any(token in blob for token in ("aria-", "accessibility", "wcag", "screen reader")):
        tags.append("accessibility")
    if any(token in blob for token in ("<form", "input", "select", "textarea", "fieldset")):
        tags.append("forms")
    if any(token in blob for token in ("<article", "<section", "<nav", "<main", "<header", "<footer")):
        tags.append("semantic")
    if not any(t in tags for t in ("accessibility", "forms", "semantic", "layout", "metadata", "tables", "media")):
        tags.append("semantic")
    return tags


def vulcan_record_to_synthetic(
    row: dict[str, Any],
    *,
    serial: int,
    source_id: str,
) -> dict[str, Any] | None:
    messages = row.get("messages")
    if not isinstance(messages, list) or len(messages) < 2:
        return None
    user_content = ""
    assistant_content = ""
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content", "")
        if role == "user" and isinstance(content, str):
            user_content = content
        if role == "assistant" and isinstance(content, str):
            assistant_content = content
    if not user_content.strip() or not assistant_content.strip():
        return None
    if not is_in_scope_front_end_code(assistant_content):
        return None
    if not has_html_document_root(assistant_content):
        return None
    instruction = ensure_imperative_instruction(user_content)
    return {
        "id": f"syn-html-{serial:04d}",
        "targetLanguage": "HTML",
        "instruction": instruction,
        "code": assistant_content,
        "tags": infer_html_tags(instruction, assistant_content),
        "metadata": {
            "author": "external-vulcan",
            "created": date.today().isoformat(),
            "source": "synthetic",
            "notes": f"external: xlelords/vulcan id={source_id}",
        },
    }


def weba11y_record_to_synthetic(
    row: dict[str, Any],
    *,
    serial: int,
) -> dict[str, Any] | None:
    prompt = row.get("prompt")
    code = row.get("code")
    if not isinstance(prompt, str) or not isinstance(code, str):
        return None
    if not prompt.strip() or not code.strip():
        return None
    if not is_in_scope_front_end_code(code):
        return None
    if not has_html_document_root(code):
        return None
    instruction = ensure_imperative_instruction(prompt)
    return {
        "id": f"syn-html-{serial:04d}",
        "targetLanguage": "HTML",
        "instruction": instruction,
        "code": code,
        "tags": infer_html_tags(instruction, code),
        "metadata": {
            "author": "external-weba11y",
            "created": date.today().isoformat(),
            "source": "synthetic",
            "notes": f"external: WebA11yBench index={serial}",
        },
    }


def iter_vulcan_records(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            record = vulcan_record_to_synthetic(row, serial=line_no, source_id=str(line_no))
            if record is not None:
                yield record


def iter_weba11y_records(path: Path, *, start_serial: int = 1) -> Iterator[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("WebA11yBench prompts_with_code.json must be a JSON array")
    serial = start_serial
    for row in data:
        record = weba11y_record_to_synthetic(row, serial=serial)
        serial += 1
        if record is not None:
            yield record


def write_raw_batches(
    records: list[dict[str, Any]],
    output_dir: Path,
    *,
    batch_size: int = 50,
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    batch_index = 0
    for offset in range(0, len(records), batch_size):
        batch_index += 1
        chunk = records[offset : offset + batch_size]
        batch_path = output_dir / f"batch-{batch_index:03d}.jsonl"
        batch_path.write_text(
            "\n".join(json.dumps(record, ensure_ascii=False) for record in chunk) + "\n",
            encoding="utf-8",
        )
    manifest = {
        "runId": output_dir.name,
        "targetLanguage": "HTML",
        "candidateCount": len(records),
        "batchCount": batch_index,
        "expansionMethod": "external-tier-a-import",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return len(records)
