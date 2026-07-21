"""Unit tests for large-site schedule loader (CPU-only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nano_orchestrator.application.large_site_schedule import (
    assert_schedule_valid,
    load_schedule,
    slot_to_task,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = ROOT / "benchmarks" / "large_site_schedule.json"


def test_schedule_valid() -> None:
    data = load_schedule(SCHEDULE)
    assert_schedule_valid(data)
    assert len(data["slots"]) <= 5


def test_schedule_one_model_per_slot() -> None:
    data = load_schedule(SCHEDULE)
    if data.get("require_unique_models", True):
        models = [s["model_id"] for s in data["slots"]]
        assert len(models) == len(set(models))


def test_normalize_adds_export_and_fixes_ftl() -> None:
    from nano_orchestrator.application.codegen_prompts import (
        extract_code,
        normalize_worker_code,
    )
    from nano_orchestrator.domain.entities import TargetLanguage

    js = normalize_worker_code(
        "function total(cart) { return 0; }\n", TargetLanguage.JAVASCRIPT
    )
    assert js.startswith("export function")
    ftl = extract_code(
        "#list items as item\n#{item.name?html}\n",
        TargetLanguage.FREEMARKER,
    )
    assert "<#list" in ftl
    assert "${item.name?html}" in ftl
    assert "</#list>" in ftl


def test_schedule_covers_html_js_ftl() -> None:
    data = load_schedule(SCHEDULE)
    langs = {s["language"] for s in data["slots"]}
    assert {"html", "javascript", "freemarker"} <= langs


def test_slot_to_task_roundtrip() -> None:
    data = load_schedule(SCHEDULE)
    task = slot_to_task(data["slots"][0])
    assert task.id == "site-home"
    assert task.language.value == "html"
    assert task.max_tokens >= 384


def test_assert_rejects_six_slots() -> None:
    data = load_schedule(SCHEDULE)
    bad = dict(data)
    bad["slots"] = list(data["slots"]) + [data["slots"][0]]
    with pytest.raises(ValueError, match="asi08"):
        assert_schedule_valid(bad)


def test_evaluate_site_quality_on_good_fixtures() -> None:
    from nano_orchestrator.application.large_site_schedule import evaluate_site_quality

    files = {
        "site-home": (
            "<!DOCTYPE html><html lang='en'><head><title>x</title></head>"
            "<body><header><nav><a href='menu.html'>Menu</a></nav></header>"
            "<main><h1>Hi</h1></main></body></html>\n"
        ),
        "site-menu": (
            "<!DOCTYPE html><html><head><title>m</title></head><body>"
            "<h1>Menu</h1><ul>"
            "<li>A $1</li><li>B $2</li><li>C $3</li><li>D $4</li><li>E $5</li>"
            "</ul><form method='post' action='/order'>"
            "<button type='submit'>Go</button></form></body></html>\n"
        ),
        "site-cart": (
            "export function addItem(cart, id, price) { cart.push({id, price, qty:1}); "
            "return cart; }\n"
            "export function removeItem(cart, id) { return cart.filter(x => x.id !== id); }\n"
            "export function total(cart) { return cart.reduce((s, x) => s + x.price * x.qty, 0); }\n"
        ),
        "site-money": (
            "export function formatMoney(amount) { return '$' + amount.toFixed(2); }\n"
        ),
        "site-ftl": "<#list items as item><li>${item.name?html}</li></#list>\n",
    }
    checks = evaluate_site_quality(files)
    assert all(checks.values()), checks


PRO_SCHEDULE = ROOT / "benchmarks" / "large_site_schedule_pro.json"


def test_pro_schedule_valid() -> None:
    data = load_schedule(PRO_SCHEDULE)
    assert_schedule_valid(data)
    assert data["kind"] == "pro_site"
    langs = {s["language"] for s in data["slots"]}
    assert {"html", "css"} <= langs
    assert all(s.get("filename") for s in data["slots"])


def test_evaluate_pro_site_quality() -> None:
    from nano_orchestrator.application.large_site_schedule import (
        evaluate_pro_site_quality,
    )

    css = (
        ":root { --accent: #c4783a; }\nbody { margin: 0; }\n"
        "nav { display: flex; }\n.hero { padding: 2rem; }\n"
        ".site-footer { padding: 1rem; }\nform { display: grid; }\n"
    )
    page = (
        "<!DOCTYPE html><html><head>"
        "<link rel='stylesheet' href='styles.css' />"
        "</head><body><nav><a href='index.html'>Home</a></nav>"
        "<main><h1>Hi</h1></main></body></html>\n"
    )
    menu = page.replace("<h1>Hi</h1>", "<ul><li>Latte $4.50</li></ul>")
    contact = page.replace("<h1>Hi</h1>", "<form method='post'><button>Send</button></form>")
    checks = evaluate_pro_site_quality(
        {
            "styles": css,
            "home": page,
            "menu": menu,
            "about": page,
            "contact": contact,
        }
    )
    assert all(checks.values()), checks


def test_css_extract_and_looks_like() -> None:
    from nano_orchestrator.application.codegen_prompts import (
        extract_code,
        looks_like_code,
    )
    from nano_orchestrator.domain.entities import TargetLanguage

    raw = "Sure, here is CSS:\n```css\n:root { --x: 1; }\nbody { color: red; }\nnav a { color: blue; }\n.hero { padding: 1rem; }\n```\n"
    code = extract_code(raw, TargetLanguage.CSS)
    assert ":root" in code
    assert looks_like_code(code, TargetLanguage.CSS)


def test_keep_alive_helpers() -> None:
    from nano_orchestrator.application.large_site_schedule import (
        next_slot_same_model,
        should_reuse_server,
    )

    assert should_reuse_server("m1", "m1", keep_alive=True) is True
    assert should_reuse_server("m1", "m2", keep_alive=True) is False
    assert should_reuse_server(None, "m1", keep_alive=True) is False
    assert should_reuse_server("m1", "m1", keep_alive=False) is False
    slots = [
        {"model_id": "a"},
        {"model_id": "a"},
        {"model_id": "b"},
    ]
    assert next_slot_same_model(slots, 0) is True
    assert next_slot_same_model(slots, 1) is False
    assert next_slot_same_model(slots, 2) is False


def test_model_server_stop_grace_params() -> None:
    import inspect

    from nano_orchestrator.infrastructure.model_server import start_server, stop_server

    assert "grace_s" in inspect.signature(stop_server).parameters
    assert "force_stop" in inspect.signature(start_server).parameters
    assert "stop_grace_s" in inspect.signature(start_server).parameters


def test_primary_worker_model() -> None:
    from nano_orchestrator.application.large_site_schedule import primary_worker_model

    assert (
        primary_worker_model(
            [{"model_id": "a"}, {"model_id": "b"}, {"model_id": "a"}]
        )
        == "a"
    )
    assert primary_worker_model([]) is None


def test_pro_f_schedule_skip_orchestrator_flag() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_f.json")
    assert_schedule_valid(data)
    assert data["speed"]["skip_orchestrator"] is True
    assert data["benchmark_id"] == "pro-site-F-fern-field"


def test_pro_g_schedule_s6_flags() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_g.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-G-beacon-dental"
    assert data["speed"]["skip_orchestrator"] is True
    assert data["speed"]["approach"] == "S6_skip_duplicate_port_kill_tighter_tokens"
    assert data["slots"][0]["max_tokens"] == 900


def test_pro_h_schedule_s7_flags() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_h.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-H-atlas-climbing"
    assert data["speed"]["skip_orchestrator"] is True
    assert data["speed"]["ctx_size"] == 2048
    assert data["speed"]["trust_start_health"] is True
    assert data["speed"]["approach"] == "S7_ctx2048_trust_start_health"


def test_pro_i_schedule_s8_flags() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_i.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-I-lumen-photo"
    assert data["speed"]["temperature"] == 0.0
    assert data["speed"]["stop_grace_s"] == 0.0
    assert data["slots"][0]["max_tokens"] == 750
    assert data["speed"]["approach"] == "S8_temp0_stop_grace0_tighter_tokens"


def test_pro_j_schedule_after_s9_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_j.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-J-copper-lantern"
    assert data["speed"]["temperature"] == 0.0
    assert data["speed"].get("top_k") is None
    assert data["speed"].get("skip_final_stop") is None
    assert data["speed"]["approach"] == "S8_after_S9_revert"


def test_pro_k_schedule_after_s10_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_k.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-K-willow-whisk"
    assert data["speed"].get("log_calls") is None
    assert data["speed"].get("cache_prompt") is None
    assert data["speed"]["approach"] == "S8_after_S10_revert"


def test_pro_l_schedule_after_s11_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_l.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-L-moss-stone"
    assert data["speed"].get("parallel_same_model_slots") is None
    assert data["speed"].get("n_parallel") is None
    assert data["speed"]["approach"] == "S8_after_S11_revert"


def test_pro_m_schedule_s12_flags() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_m.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-M-bright-harbor"
    assert data["speed"]["parallel_same_model_slots"] is True
    assert data["speed"]["n_parallel"] == 4
    assert data["speed"]["ctx_size"] == 8192
    assert data["speed"]["approach"] == "S12_parallel_html_ctx8192_np4"


def test_pro_n_schedule_s13_flags() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_n.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-N-northline-bike"
    assert data["speed"]["parallel_all_slots"] is True
    assert data["speed"]["n_parallel"] == 5
    assert data["speed"]["ctx_size"] == 10240
    assert data["speed"]["approach"] == "S13_parallel_all_ctx10240_np5"


def test_pro_o_schedule_after_s14_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_o.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-O-marble-rye"
    assert data["speed"].get("skip_final_stop") is None
    assert data["slots"][0]["max_tokens"] == 780
    assert data["speed"]["parallel_all_slots"] is True
    assert data["speed"]["approach"] == "S13_after_S14_revert"


def test_pro_p_schedule_after_s15_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_p.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-P-pinecrest-vet"
    assert data["speed"].get("flash_attn") is None
    assert data["speed"].get("kv_unified") is None
    assert data["speed"]["parallel_all_slots"] is True
    assert data["speed"]["n_parallel"] == 5
    assert data["speed"]["ctx_size"] == 10240
    assert data["slots"][0]["max_tokens"] == 780
    assert data["speed"]["approach"] == "S13_after_S15_revert"


def test_pro_q_schedule_after_s16_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_q.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-Q-tidepool-surf"
    assert data["speed"].get("batch_size") is None
    assert data["speed"].get("ubatch_size") is None
    assert data["speed"]["parallel_all_slots"] is True
    assert data["speed"]["n_parallel"] == 5
    assert data["speed"]["ctx_size"] == 10240
    assert data["slots"][0]["max_tokens"] == 780
    assert data["speed"]["approach"] == "S13_after_S16_revert"


def test_pro_r_schedule_after_s17_revert() -> None:
    data = load_schedule(ROOT / "benchmarks" / "large_site_schedule_pro_r.json")
    assert_schedule_valid(data)
    assert data["benchmark_id"] == "pro-site-R-brickhouse-brew"
    assert data["speed"].get("health_sleep") is None
    assert data["speed"].get("skip_final_stop") is None
    assert data["speed"]["parallel_all_slots"] is True
    assert data["speed"]["n_parallel"] == 5
    assert data["speed"]["ctx_size"] == 10240
    assert data["slots"][0]["max_tokens"] == 780
    assert data["speed"]["approach"] == "S13_after_S17_revert"


def test_bind_orch_plan_maps_by_id() -> None:
    from nano_orchestrator.application.large_site_schedule import bind_orch_plan_to_slots

    slots = [
        {"id": "site-home", "model_id": "m1", "language": "html", "max_tokens": 100},
        {"id": "site-cart", "model_id": "m2", "language": "javascript", "max_tokens": 100},
    ]
    orch = [
        {"id": "site-home", "language": "html", "prompt": "orch home", "max_tokens": 300},
        {"id": "site-cart", "language": "javascript", "prompt": "orch cart", "max_tokens": 50},
    ]
    merged, meta = bind_orch_plan_to_slots(slots, orch)
    assert meta["bound"] == 2
    assert meta["mode"] == "orch_bound"
    assert merged[0]["model_id"] == "m1"
    assert merged[0]["orch_prompt"] == "orch home"
    assert merged[0]["max_tokens"] == 300
    assert merged[1]["max_tokens"] == 100


def test_coerce_microtask_missing_fields() -> None:
    from nano_orchestrator.domain.microtask_parser import parse_microtasks_json

    raw = '[{"id":"t1","language":"js","prompt":"do thing"}]'
    result = parse_microtasks_json(raw)
    assert result.is_ok()
    task = result.value[0]  # type: ignore[index]
    assert task.role.value == "coder"
    assert task.language.value == "javascript"
    assert task.acceptance == ["syntax_valid"]
