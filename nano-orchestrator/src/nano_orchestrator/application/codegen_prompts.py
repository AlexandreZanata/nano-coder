"""Prompt building and code extraction for bake-off workers."""

from __future__ import annotations

import re

from nano_orchestrator.domain.entities import MicroTask, TargetLanguage

_FENCE_RE = re.compile(r"```(?:javascript|js|html|htm|ftl|freemarker|text)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def build_worker_prompt(task: MicroTask) -> str:
    lang = task.language.value
    constraints = "; ".join(task.constraints) if task.constraints else "none"
    return (
        "You are a careful coding assistant. Output ONLY the code for the task.\n"
        "Do not explain. Prefer a single fenced code block.\n\n"
        f"Language: {lang}\n"
        f"Constraints: {constraints}\n"
        f"Acceptance: {', '.join(task.acceptance)}\n\n"
        f"Task:\n{task.prompt}\n"
    )


def build_orchestrator_prompt(user_request: str, max_tasks: int = 5) -> str:
    example = (
        '[{"id":"t1","role":"coder","language":"javascript",'
        '"prompt":"Export function clamp(n, min, max)",'
        '"constraints":["ES modules"],"acceptance":["syntax_valid"],"max_tokens":128},'
        '{"id":"t2","role":"coder","language":"html",'
        '"prompt":"Write a form with a Submit button",'
        '"constraints":["semantic HTML5"],"acceptance":["syntax_valid"],"max_tokens":128}]'
    )
    return (
        "You split coding work into MicroTask JSON objects.\n"
        f"Return ONLY a JSON array with at most {max_tasks} objects.\n"
        "Each object keys: id, role, language, prompt, constraints, acceptance, max_tokens.\n"
        'role must be "coder". language must be javascript|html|freemarker.\n'
        "Example output:\n"
        f"{example}\n\n"
        f"User request:\n{user_request}\n"
        "JSON array:"
    )


def extract_code(raw: str, language: TargetLanguage) -> str:
    """Pull first fenced block, else strip chatter and return remainder."""
    match = _FENCE_RE.search(raw)
    if match:
        return match.group(1).strip() + "\n"
    text = raw.strip()
    # Drop common preambles
    for marker in ("Here is", "Here's", "Sure,", "Certainly"):
        if text.startswith(marker):
            nl = text.find("\n")
            if nl != -1:
                text = text[nl + 1 :].strip()
    if language is TargetLanguage.JAVASCRIPT and "export " in text:
        idx = text.find("export ")
        text = text[idx:]
    elif language is TargetLanguage.HTML:
        idx = text.find("<")
        if idx != -1:
            text = text[idx:]
    elif language is TargetLanguage.FREEMARKER:
        for token in ("<#", "${", "<"):
            idx = text.find(token)
            if idx != -1:
                text = text[idx:]
                break
    return text.strip() + ("\n" if text.strip() else "")
