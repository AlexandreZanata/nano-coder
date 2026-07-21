"""Large-site multi-model schedule helpers (ASI08 ≤5 slots)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from nano_orchestrator.application.codegen_prompts import looks_like_code
from nano_orchestrator.domain.entities import MicroTask, TargetLanguage, WorkerRole


def load_schedule(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def slot_to_task(slot: dict) -> MicroTask:
    return MicroTask(
        id=str(slot["id"]),
        role=WorkerRole.CODER,
        language=TargetLanguage(slot["language"]),
        prompt=str(slot["prompt"]),
        constraints=list(slot.get("constraints") or []),
        acceptance=list(slot.get("acceptance") or ["syntax_valid"]),
        max_tokens=int(slot.get("max_tokens") or 384),
    )


def slot_filenames(slots: list[dict]) -> dict[str, str]:
    """Optional explicit output filenames from schedule slots."""
    out: dict[str, str] = {}
    for slot in slots:
        name = slot.get("filename")
        if name:
            out[str(slot["id"])] = str(name)
    return out


def should_reuse_server(
    loaded_model_id: str | None,
    next_model_id: str,
    *,
    keep_alive: bool,
) -> bool:
    """Reuse running llama-server when consecutive slots share a model."""
    if not keep_alive or not loaded_model_id:
        return False
    return loaded_model_id == next_model_id


def next_slot_same_model(slots: list[dict], index: int) -> bool:
    """True if slots[index+1] uses the same model_id as slots[index]."""
    if index < 0 or index + 1 >= len(slots):
        return False
    return str(slots[index]["model_id"]) == str(slots[index + 1]["model_id"])


def bind_orch_plan_to_slots(
    slots: list[dict],
    orch_tasks: list[dict] | None,
) -> tuple[list[dict], dict]:
    """Keep unique model_id per slot; attach orch prompt metadata by language/id.

    Worker prompts stay canonical (quality), but we record which orch MicroTask
    mapped to each slot so the schedule still 'separates' via the orchestrator.
    """
    meta: dict = {"bound": 0, "mode": "canonical_only", "bindings": []}
    if not orch_tasks:
        return [dict(s) for s in slots], meta

    by_id = {str(t.get("id")): t for t in orch_tasks if t.get("id")}
    by_lang: dict[str, list[dict]] = {}
    for t in orch_tasks:
        lang = str(t.get("language") or "")
        by_lang.setdefault(lang, []).append(t)

    out: list[dict] = []
    for slot in slots:
        merged = dict(slot)
        ot = by_id.get(str(slot["id"]))
        if ot is None:
            pool = by_lang.get(str(slot["language"])) or []
            ot = pool.pop(0) if pool else None
        if ot is not None:
            merged["orch_task_id"] = ot.get("id")
            merged["orch_prompt"] = ot.get("prompt")
            # Prefer richer max_tokens
            merged["max_tokens"] = max(
                int(slot.get("max_tokens") or 256),
                int(ot.get("max_tokens") or 0),
            )
            meta["bound"] += 1
            meta["bindings"].append(
                {
                    "slot_id": slot["id"],
                    "model_id": slot["model_id"],
                    "orch_task_id": ot.get("id"),
                    "orch_language": ot.get("language"),
                }
            )
        out.append(merged)
    meta["mode"] = "orch_bound" if meta["bound"] else "canonical_only"
    return out, meta


def assert_schedule_valid(schedule: dict) -> None:
    slots = list(schedule.get("slots") or [])
    if not slots or len(slots) > 5:
        raise ValueError(f"asi08_cap:slots={len(slots)}")
    models = [str(s["model_id"]) for s in slots]
    require_unique = bool(schedule.get("require_unique_models", True))
    if require_unique and len(models) != len(set(models)):
        raise ValueError("duplicate_model_in_schedule")
    langs = {str(s["language"]) for s in slots}
    kind = str(schedule.get("kind") or "bakeoff")
    if kind == "pro_site":
        required = {"html", "css"}
    else:
        required = {"html", "javascript", "freemarker"}
    if not required <= langs:
        raise ValueError(f"missing_languages:{required - langs}")


def evaluate_site_quality(files: dict[str, str]) -> dict[str, bool]:
    """Content checklist beyond sandbox Pass@1 (bakeoff schedule)."""
    home = files.get("site-home", "")
    menu = files.get("site-menu", "")
    cart = files.get("site-cart", "")
    money = files.get("site-money", "")
    ftl = files.get("site-ftl", "")
    home_ok = looks_like_code(home, TargetLanguage.HTML)
    menu_ok = looks_like_code(menu, TargetLanguage.HTML)
    checks = {
        "home_complete_html": home_ok,
        "home_has_nav": home_ok and bool(re.search(r"<nav[\s>]", home, re.I)),
        "menu_complete_html": menu_ok,
        "menu_has_prices": menu_ok and bool(re.search(r"\$\d", menu)),
        "menu_has_5_items": menu_ok and len(re.findall(r"<li[\s>]", menu, re.I)) >= 5,
        "cart_exports": looks_like_code(cart, TargetLanguage.JAVASCRIPT)
        and "addItem" in cart
        and "removeItem" in cart
        and "total" in cart,
        "money_formats": looks_like_code(money, TargetLanguage.JAVASCRIPT)
        and "toFixed" in money,
        "ftl_list_html": looks_like_code(ftl, TargetLanguage.FREEMARKER),
    }
    return checks


def evaluate_pro_site_quality(files: dict[str, str]) -> dict[str, bool]:
    """Checklist for professional multi-page HTML+CSS site."""
    css = files.get("styles") or files.get("styles.css") or ""
    pages = {
        "index": files.get("home") or files.get("index") or files.get("index.html") or "",
        "menu": files.get("menu") or files.get("menu.html") or "",
        "about": files.get("about") or files.get("about.html") or "",
        "contact": files.get("contact") or files.get("contact.html") or "",
    }
    css_ok = looks_like_code(css, TargetLanguage.CSS)
    checks: dict[str, bool] = {
        "styles_complete": css_ok,
        "styles_has_root": css_ok and ":root" in css,
        "styles_has_nav": css_ok and "nav" in css.lower(),
        "styles_has_hero": css_ok and ".hero" in css.lower(),
        "styles_has_footer": css_ok and "site-footer" in css,
        "styles_has_form": css_ok and "form" in css.lower(),
    }
    for key, html in pages.items():
        ok = looks_like_code(html, TargetLanguage.HTML)
        checks[f"{key}_complete_html"] = ok
        checks[f"{key}_links_css"] = ok and (
            'href="styles.css"' in html or "href='styles.css'" in html
        )
        checks[f"{key}_has_nav"] = ok and bool(re.search(r"<nav[\s>]", html, re.I))
    menu = pages["menu"]
    checks["menu_has_prices"] = bool(re.search(r"\$\d", menu))
    checks["contact_has_form"] = bool(re.search(r"<form[\s>]", pages["contact"], re.I))
    return checks
