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


def assert_schedule_valid(schedule: dict) -> None:
    slots = list(schedule.get("slots") or [])
    if not slots or len(slots) > 5:
        raise ValueError(f"asi08_cap:slots={len(slots)}")
    models = [str(s["model_id"]) for s in slots]
    require_unique = bool(schedule.get("require_unique_models", True))
    if require_unique and len(models) != len(set(models)):
        raise ValueError("duplicate_model_in_schedule")
    langs = {str(s["language"]) for s in slots}
    required = {"html", "javascript", "freemarker"}
    if not required <= langs:
        raise ValueError(f"missing_languages:{required - langs}")


def evaluate_site_quality(files: dict[str, str]) -> dict[str, bool]:
    """Content checklist beyond sandbox Pass@1."""
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
