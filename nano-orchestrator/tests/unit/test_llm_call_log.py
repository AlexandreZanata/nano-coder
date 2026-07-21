"""LLM call log + LlamaCppAdapter logging (T-045)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from nano_orchestrator.infrastructure.llamacpp_adapter import LlamaCppAdapter
from nano_orchestrator.infrastructure.llm_call_log import append_llm_call, prompt_hash


def test_given_prompt_when_append_then_jsonl_has_hash_latency_model(tmp_path: Path) -> None:
    log_path = tmp_path / "llm_calls.jsonl"
    prompt = "hello worker"
    path = append_llm_call(
        model_id="qwen25-coder-0.5b",
        prompt=prompt,
        latency_ms=42,
        ok=True,
        tokens_predicted=7,
        log_path=log_path,
    )
    assert path == log_path
    line = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert line["model_id"] == "qwen25-coder-0.5b"
    assert line["prompt_hash"] == prompt_hash(prompt)
    assert line["latency_ms"] == 42
    assert line["ok"] is True
    assert "prompt" not in line


def test_given_generate_when_ok_then_adapter_appends_log(tmp_path: Path) -> None:
    log_path = tmp_path / "calls.jsonl"
    adapter = LlamaCppAdapter(
        "http://127.0.0.1:9",
        model_id="smollm3-3b",
        log_calls=True,
        log_path=log_path,
    )
    body = json.dumps({"content": "ok", "tokens_predicted": 3}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = adapter.generate_detailed("decompose this", max_tokens=16)
    assert result.is_ok()
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["model_id"] == "smollm3-3b"
    assert records[0]["prompt_hash"] == prompt_hash("decompose this")
    assert records[0]["ok"] is True
    assert "latency_ms" in records[0]
