"""Prompt building and code extraction for bake-off workers."""

from __future__ import annotations

import re

from nano_orchestrator.domain.entities import MicroTask, TargetLanguage

_FENCE_RE = re.compile(
    r"```(?:javascript|js|html|htm|css|ftl|freemarker|text)?\s*\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)
_TRAILING_CHATTER = re.compile(
    r"\n(?:Solution:|Now, write|The code must|Expected output|Test case:).*\Z",
    re.DOTALL | re.IGNORECASE,
)


def build_worker_prompt(task: MicroTask) -> str:
    lang = task.language.value
    constraints = "; ".join(task.constraints) if task.constraints else "none"
    return (
        "You are a careful coding assistant. Output ONLY the code for the task.\n"
        "Do not explain. Prefer a single fenced code block.\n"
        "Do not leave empty function bodies or TODO stubs.\n"
        "Do not repeat instructions.\n\n"
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
        'role must be "coder". language must be javascript|html|freemarker|css.\n'
        "Example output:\n"
        f"{example}\n\n"
        f"User request:\n{user_request}\n"
        "JSON array:"
    )


def extract_code(raw: str, language: TargetLanguage) -> str:
    """Pull first fenced block, else strip chatter and return remainder."""
    match = _FENCE_RE.search(raw)
    if match and match.group(1).strip():
        text = match.group(1).strip()
    else:
        text = raw.strip()
        # Drop empty/broken fences like "```\n```"
        text = re.sub(r"^```(?:\w+)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        for marker in ("Here is", "Here's", "Sure,", "Certainly", "The menu page"):
            if text.startswith(marker):
                nl = text.find("\n")
                if nl != -1:
                    text = text[nl + 1 :].strip()
        if language is TargetLanguage.JAVASCRIPT:
            text = _slice_from(text, ("export ", "function ", "const ", "class "))
        elif language is TargetLanguage.HTML:
            text = _slice_html(text)
        elif language is TargetLanguage.CSS:
            text = _slice_css(text)
        elif language is TargetLanguage.FREEMARKER:
            text = _slice_from(text, ("<#", "#list", "${", "<"))
    text = _TRAILING_CHATTER.sub("", text).strip()
    if language is TargetLanguage.FREEMARKER:
        text = _first_ftl_block(text)
    if language is TargetLanguage.HTML:
        text = _trim_html_document(text)
    if language is TargetLanguage.JAVASCRIPT:
        text = _trim_js_module(text)
    if language is TargetLanguage.CSS:
        text = _trim_css(text)
    return normalize_worker_code(text, language)


def looks_like_code(code: str, language: TargetLanguage) -> bool:
    c = code.strip()
    if len(c) < 8:
        return False
    if language is TargetLanguage.JAVASCRIPT:
        if "your code here" in c.lower() or "TODO" in c:
            return False
        has_export = "export " in c
        has_fn = "function " in c or "=>" in c
        return has_export and has_fn and "{" in c and "}" in c
    if language is TargetLanguage.HTML:
        lower = c.lower()
        return ("<!doctype html>" in lower or "<html" in lower) and "</html>" in lower
    if language is TargetLanguage.CSS:
        lower = c.lower()
        return (
            "{" in c
            and "}" in c
            and "<html" not in lower
            and any(t in lower for t in ("body", "nav", ":root", ".hero"))
        )
    if language is TargetLanguage.FREEMARKER:
        return "<#list" in c.lower() and "?html" in c.lower()
    return False


def normalize_worker_code(code: str, language: TargetLanguage) -> str:
    """Post-extract repairs for common small-model mistakes."""
    text = code.strip()
    if not text:
        return ""
    if language is TargetLanguage.JAVASCRIPT:
        if "export " not in text and re.search(r"^function\s+", text, re.M):
            text = re.sub(
                r"^(async\s+)?function\s+",
                r"export \1function ",
                text,
                flags=re.M,
            )
    if language is TargetLanguage.FREEMARKER:
        text = text.replace("#{", "${")
        stripped = text.lstrip()
        if stripped.startswith("#list"):
            text = "<" + stripped
        elif stripped.startswith("list "):
            text = "<#list " + stripped[5:]
        # Ensure opening directive closes with >
        text = re.sub(
            r"^(<#list\s+[^\n>]+)\s*\n",
            r"\1>\n",
            text,
            count=1,
            flags=re.I,
        )
        if "<#list" in text.lower() and "</#list>" not in text.lower():
            text = text.rstrip() + "\n</#list>"
        text = _first_ftl_block(text)
    return text + ("\n" if text else "")


def _slice_from(text: str, tokens: tuple[str, ...]) -> str:
    best = -1
    for token in tokens:
        idx = text.find(token)
        if idx != -1 and (best < 0 or idx < best):
            best = idx
    return text[best:] if best >= 0 else text


def _slice_html(text: str) -> str:
    lower = text.lower()
    for token in ("<!doctype", "<html", "<form", "<header", "<main", "<ul", "<section"):
        idx = lower.find(token)
        if idx != -1:
            return text[idx:]
    idx = text.find("<")
    return text[idx:] if idx != -1 else text


def _slice_css(text: str) -> str:
    lower = text.lower()
    for token in (":root", "body", "*", "html", ".hero", "nav", "/*"):
        idx = lower.find(token)
        if idx != -1:
            return text[idx:]
    brace = text.find("{")
    return text[: brace].rsplit("\n", 1)[-1] + text[brace:] if brace > 0 else text


def _trim_css(text: str) -> str:
    cut = re.search(
        r"\n(?:Here is the|Here is|The CSS|Language:|Task:|Constraints:|Acceptance:|Now write)",
        text,
        re.I,
    )
    if cut:
        text = text[: cut.start()].strip()
    first = text.find(":root")
    if first >= 0:
        second = text.find(":root", first + 5)
        if second > 0:
            text = text[:second].strip()
    return text.strip()


def _trim_html_document(text: str) -> str:
    lower = text.lower()
    start = 0
    for token in ("<!doctype", "<html"):
        idx = lower.find(token)
        if idx != -1:
            start = idx
            break
    # FIRST closing html — models often re-echo the prompt afterward
    end = lower.find("</html>", start)
    if end != -1:
        return text[start : end + len("</html>")].strip()
    return text[start:].strip()


def _trim_js_module(text: str) -> str:
    # Drop leading prose lines before first export/function
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith(("export ", "function ", "const ", "class ", "//")):
            start = i
            break
    body = "\n".join(lines[start:]).strip()
    cut = re.search(r"\nThe code must\b|\nI have to write\b|\nLanguage:\b|\nTask:\b", body)
    if cut:
        body = body[: cut.start()].strip()
    # Deduplicate repeated export function blocks (keep prefix until balance repeats)
    if body.count("export function") > 1:
        body = _first_balanced_exports(body)
    return body


def _first_balanced_exports(text: str) -> str:
    """Keep code through the first contiguous export block set (brace balanced)."""
    depth = 0
    started = False
    out: list[str] = []
    for line in text.splitlines(keepends=True):
        if not started and line.lstrip().startswith("export "):
            started = True
        if not started:
            continue
        # Stop if a second identical export function name appears after closed braces
        if depth == 0 and out and line.lstrip().startswith("export function"):
            name = re.match(r"\s*export function\s+([A-Za-z0-9_]+)", line)
            already = "".join(out)
            if name and re.search(
                rf"export function\s+{re.escape(name.group(1))}\b", already
            ):
                break
        out.append(line)
        depth += line.count("{") - line.count("}")
        if started and depth <= 0 and "{" in "".join(out):
            depth = 0
    return "".join(out).strip()


def _first_ftl_block(text: str) -> str:
    lower = text.lower()
    start = lower.find("<#list")
    if start < 0:
        return text
    end = lower.find("</#list>", start)
    if end < 0:
        return text[start:].strip()
    return text[start : end + len("</#list>")].strip()
